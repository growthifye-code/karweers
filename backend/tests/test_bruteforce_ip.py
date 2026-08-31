"""Verify real-client-IP based brute-force lockout in server._client_ip / _login_identifier / register_failed_login."""
import os
import sys
import asyncio
import pytest
from pathlib import Path

# Make backend importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import HTTPException

import pytest_asyncio  # noqa: F401
import server  # noqa: E402
from server import (
    _client_ip, _login_identifier, check_login_lockout,
    register_failed_login, clear_login_attempts, LOGIN_MAX_ATTEMPTS,
)


def db():
    """Always return the current (rebound) server.db to avoid stale loop binding."""
    return server.db


def make_request(headers=None, peer_host="10.0.0.1"):
    """Build a minimal object mimicking starlette Request for the helpers under test."""
    headers = headers or {}

    class _H:
        def __init__(self, d):
            self._d = {k.lower(): v for k, v in d.items()}

        def get(self, k, default=None):
            return self._d.get(k.lower(), default)

    class _C:
        def __init__(self, h): self.host = h

    class _Req:
        def __init__(self):
            self.headers = _H(headers)
            self.client = _C(peer_host)

    return _Req()


TEST_EMAILS = ["test_bf_user1@example.com", "test_bf_user2@example.com"]
TEST_IPS = ["203.0.113.10", "203.0.113.20", "198.51.100.5"]


@pytest_asyncio.fixture(autouse=True)
async def _cleanup():
    # pre + post cleanup
    for ip in TEST_IPS:
        await db().login_attempts.delete_many({"ip": ip})
        await db().blocked_ips.delete_many({"ip": ip})
    for email in TEST_EMAILS:
        await db().login_attempts.delete_many({"email": email})
    await db().security_alerts.delete_many({"email": {"$in": TEST_EMAILS}})
    yield
    for ip in TEST_IPS:
        await db().login_attempts.delete_many({"ip": ip})
        await db().blocked_ips.delete_many({"ip": ip})
    for email in TEST_EMAILS:
        await db().login_attempts.delete_many({"email": email})
    await db().security_alerts.delete_many({"email": {"$in": TEST_EMAILS}})


# ---------- _client_ip precedence ----------
def test_client_ip_from_xff_first():
    req = make_request(headers={"X-Forwarded-For": "203.0.113.10, 10.0.0.99, 172.16.0.1",
                                "X-Real-IP": "198.51.100.5"},
                       peer_host="10.244.0.1")
    assert _client_ip(req) == "203.0.113.10"


def test_client_ip_from_xri_when_no_xff():
    req = make_request(headers={"X-Real-IP": "198.51.100.5"}, peer_host="10.244.0.1")
    assert _client_ip(req) == "198.51.100.5"


def test_client_ip_falls_back_to_peer():
    req = make_request(headers={}, peer_host="10.244.0.1")
    assert _client_ip(req) == "10.244.0.1"


# ---------- _login_identifier uses real client IP ----------
def test_login_identifier_uses_xff_not_proxy():
    real_ip = "203.0.113.10"
    proxy_ip = "10.244.0.5"
    req = make_request(headers={"X-Forwarded-For": f"{real_ip}, {proxy_ip}"}, peer_host=proxy_ip)
    ident = _login_identifier(req, TEST_EMAILS[0])
    assert ident == f"{real_ip}:{TEST_EMAILS[0]}"
    assert proxy_ip not in ident


def test_different_client_ips_produce_different_identifiers():
    email = TEST_EMAILS[0]
    proxy = "10.244.0.5"
    r1 = make_request(headers={"X-Forwarded-For": f"{TEST_IPS[0]}, {proxy}"}, peer_host=proxy)
    r2 = make_request(headers={"X-Forwarded-For": f"{TEST_IPS[1]}, {proxy}"}, peer_host=proxy)
    assert _login_identifier(r1, email) != _login_identifier(r2, email)


# ---------- Brute-force lockout ----------
@pytest.mark.asyncio
async def test_lockout_after_max_attempts_and_release_on_clear():
    email = TEST_EMAILS[0]
    ip = TEST_IPS[0]
    req = make_request(headers={"X-Forwarded-For": f"{ip}, 10.244.0.5"}, peer_host="10.244.0.5")
    ident = _login_identifier(req, email)
    assert ident.startswith(ip + ":")

    # 5 failures => lockout
    for _ in range(LOGIN_MAX_ATTEMPTS):
        await register_failed_login(ident, ip, email)

    doc = await db().login_attempts.find_one({"identifier": ident})
    assert doc is not None, "login_attempts doc must exist"
    assert doc.get("locked_until"), "locked_until must be set after 5 fails"

    # check_login_lockout must raise 429 with Retry-After
    with pytest.raises(HTTPException) as ei:
        await check_login_lockout(ident)
    assert ei.value.status_code == 429
    assert "Retry-After" in (ei.value.headers or {})

    # clear releases lock
    await clear_login_attempts(ident)
    assert await db().login_attempts.find_one({"identifier": ident}) is None
    # no exception after clear
    await check_login_lockout(ident)


@pytest.mark.asyncio
async def test_two_real_ips_same_email_isolated():
    """Legit user (IP2) must NOT be locked out when attacker (IP1) is locked (same proxy, same email)."""
    email = TEST_EMAILS[1]
    proxy = "10.244.0.5"
    attacker_ip, victim_ip = TEST_IPS[0], TEST_IPS[1]

    r_attacker = make_request(headers={"X-Forwarded-For": f"{attacker_ip}, {proxy}"}, peer_host=proxy)
    r_victim = make_request(headers={"X-Forwarded-For": f"{victim_ip}, {proxy}"}, peer_host=proxy)

    id_att = _login_identifier(r_attacker, email)
    id_vic = _login_identifier(r_victim, email)
    assert id_att != id_vic

    # Lock attacker
    for _ in range(LOGIN_MAX_ATTEMPTS):
        await register_failed_login(id_att, attacker_ip, email)

    with pytest.raises(HTTPException) as ei:
        await check_login_lockout(id_att)
    assert ei.value.status_code == 429

    # Victim must be unaffected
    await check_login_lockout(id_vic)  # no raise
    assert await db().login_attempts.find_one({"identifier": id_vic}) is None
