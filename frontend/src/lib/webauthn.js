function b64uToBuf(b64u) {
  const pad = "=".repeat((4 - (b64u.length % 4)) % 4);
  const b64 = (b64u + pad).replace(/-/g, "+").replace(/_/g, "/");
  const s = atob(b64);
  const buf = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) buf[i] = s.charCodeAt(i);
  return buf.buffer;
}

function bufToB64u(buf) {
  const bytes = new Uint8Array(buf);
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function credToJSON(cred) {
  const r = cred.response;
  const out = {
    id: cred.id,
    rawId: bufToB64u(cred.rawId),
    type: cred.type,
    clientExtensionResults: cred.getClientExtensionResults ? cred.getClientExtensionResults() : {},
    authenticatorAttachment: cred.authenticatorAttachment || null,
    response: {},
  };
  if (r.attestationObject) {
    out.response = {
      clientDataJSON: bufToB64u(r.clientDataJSON),
      attestationObject: bufToB64u(r.attestationObject),
      transports: r.getTransports ? r.getTransports() : [],
    };
  } else {
    out.response = {
      clientDataJSON: bufToB64u(r.clientDataJSON),
      authenticatorData: bufToB64u(r.authenticatorData),
      signature: bufToB64u(r.signature),
      userHandle: r.userHandle ? bufToB64u(r.userHandle) : null,
    };
  }
  return out;
}

export function passkeySupported() {
  return typeof window !== "undefined" && !!window.PublicKeyCredential;
}

export async function registerPasskey(options) {
  options.challenge = b64uToBuf(options.challenge);
  options.user.id = b64uToBuf(options.user.id);
  if (options.excludeCredentials) options.excludeCredentials = options.excludeCredentials.map((c) => ({ ...c, id: b64uToBuf(c.id) }));
  const cred = await navigator.credentials.create({ publicKey: options });
  return credToJSON(cred);
}

export async function authPasskey(options) {
  options.challenge = b64uToBuf(options.challenge);
  if (options.allowCredentials) options.allowCredentials = options.allowCredentials.map((c) => ({ ...c, id: b64uToBuf(c.id) }));
  const cred = await navigator.credentials.get({ publicKey: options });
  return credToJSON(cred);
}
