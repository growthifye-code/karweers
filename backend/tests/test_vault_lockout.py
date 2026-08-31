import asyncio
from fastapi import HTTPException


class FakeURL:
    path = "/api/admin/vault/unlock/totp"
    query = ""


class FakeReq:
    def __init__(self, ip="203.0.113.9"):
        self.headers = {"x-forwarded-for": ip}
        self.url = FakeURL()
        self.client = type("c", (), {"host": ip})()
        self.cookies = {}


async def main():
    import server
    email = "vaulttest@example.com"
    await server.db.vault_lockouts.delete_one({"email": email})
    req = FakeReq()

    # 4 fails: not frozen yet
    for i in range(4):
        await server.register_vault_fail(email, req, "wrong authenticator code")
    frozen, secs, fails = await server._vault_lock_state(email)
    assert not frozen and fails == 4, (frozen, fails)
    # check_vault_lockout should NOT raise
    await server.check_vault_lockout(email)
    print("PASS: 4 fails not frozen, fails=4")

    # 5th fail: freeze
    await server.register_vault_fail(email, req, "wrong authenticator code")
    frozen, secs, fails = await server._vault_lock_state(email)
    assert frozen and secs > 0, (frozen, secs)
    print(f"PASS: frozen after 5 fails, seconds_left={secs}")

    # check_vault_lockout raises 429 with Retry-After
    try:
        await server.check_vault_lockout(email)
        assert False, "expected 429"
    except HTTPException as e:
        assert e.status_code == 429 and "Retry-After" in (e.headers or {}), (e.status_code, e.headers)
        print("PASS: check_vault_lockout raises 429 + Retry-After while frozen")

    # clear releases the freeze
    await server.clear_vault_fails(email)
    frozen, secs, fails = await server._vault_lock_state(email)
    assert not frozen and fails == 0
    await server.check_vault_lockout(email)
    print("PASS: clear_vault_fails releases the freeze")

    # cleanup any alert/audit test noise
    await server.db.vault_lockouts.delete_one({"email": email})
    await server.db.security_alerts.delete_many({"email": email})
    await server.db.audit_log.delete_many({"actor": email})
    print("ALL VAULT LOCKOUT TESTS PASSED")


asyncio.run(main())
