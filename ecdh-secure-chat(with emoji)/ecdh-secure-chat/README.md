# ECDH-based secure chat using the Web Crypto API
Networking & Cyber Security lab - Exp 2: Diffie-Hellman Key Exchange.

Two browser tabs (peers) generate ECDH (P-256) key pairs, swap public keys through a relay
server, derive the same AES-256-GCM key independently, and chat with encrypted messages.

## Run
1. Install Node.js 16+ (https://nodejs.org). No other packages needed.
2. In this folder run: `node server.js`  (or `npm start`)
3. Open http://localhost:3000 in TWO tabs/windows, click **Connect** in both (same room name).
4. Verify both tabs show the identical shared key / fingerprint, then chat.
5. Watch the terminal: the server only sees public keys, IVs and ciphertext.
6. Click **Send tampered** to see AES-GCM reject a modified message.

Use `localhost` (a secure context); Web Crypto is disabled on plain http://<LAN-IP>.
Change port: `PORT=4000 node server.js` (Windows PowerShell: `$env:PORT=4000; node server.js`).

## Run without Node.js (Python 3.8+, standard library only)
`python server.py`  (Windows: `py server.py`; macOS/Linux: `python3 server.py`), then open http://localhost:3000
in two tabs. Same page, same behaviour; only the relay server differs. Port: `PORT=4000 python3 server.py`.

## Files
- `server.py` - Python alternative to server.js
- `server.js` - static file server + SSE relay (room limit: 2 peers)
- `public/index.html` - UI and all crypto (crypto.subtle: generateKey, deriveKey, encrypt, decrypt)

## Protocol
hello{pubA} -> pub{pubB} -> both: deriveKey(ECDH, own private, peer public) -> AES-GCM key
msg{iv, ciphertext+tag} with a fresh random 12-byte IV per message.

## Limits (good viva points)
Unauthenticated ECDH is open to man-in-the-middle; compare key fingerprints out of band, or sign keys
(ECDSA/certificates). No forward secrecy per message (a ratchet like Signal's would add it).
