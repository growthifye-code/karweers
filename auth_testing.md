# Auth-Gated App Testing Playbook (Emergent Google Auth)

This app supports BOTH:
- JWT email/password auth (localStorage `sk_token`, sent as `Authorization: Bearer`)
- Emergent Google Auth (httpOnly cookie `session_token`, stored in `user_sessions`)

`/api/auth/me` resolves either. Protected routes: `/dashboard` (client), `/admin` (admin).

## Step 1: Create Google Test User & Session (for cookie-based flow)
```
mongosh --eval "
use('test_database');
var userId = 'user_' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  id: userId,
  email: 'test.google.' + Date.now() + '@example.com',
  name: 'Google Test User',
  picture: 'https://via.placeholder.com/150',
  role: 'client',
  auth: 'google',
  created_at: new Date().toISOString()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000).toISOString(),
  created_at: new Date().toISOString()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Backend API test with session token (Bearer works too)
```
curl -X GET "$API_URL/api/auth/me" -H "Authorization: Bearer <SESSION_TOKEN>"
curl -X GET "$API_URL/api/learning/recommended?limit=4" -H "Authorization: Bearer <SESSION_TOKEN>"
curl -X POST "$API_URL/api/track" -H "Authorization: Bearer <SESSION_TOKEN>" -H "Content-Type: application/json" -d '{"kind":"service","ref":"re-storage-hydrogen"}'
```

## Step 3: Browser testing (cookie)
```
await page.context.add_cookies([{
  "name": "session_token", "value": "<SESSION_TOKEN>",
  "domain": "<preview-host>", "path": "/",
  "httpOnly": True, "secure": True, "sameSite": "None"
}])
await page.goto("<preview-url>/dashboard")
```

## Notes
- Google OAuth redirect flow itself (auth.emergentagent.com) cannot be automated; use the session injection above.
- `Continue with Google` button testids: `google-login-btn`, `google-register-btn`.
- Callback route: any URL with `#session_id=...` renders AuthCallback which POSTs `/api/auth/session`.
- Clean up: `db.users.deleteMany({email:/test\.google\./}); db.user_sessions.deleteMany({session_token:/test_session/});`
