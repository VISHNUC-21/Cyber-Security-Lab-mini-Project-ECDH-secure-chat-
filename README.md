 How to run it : ->
 STEPs :
1. Unzip the folder, open a terminal (cmd) inside ecdh-secure-chat, and run node server.py with command >python server.py
2. Open http://localhost:3000 in two tabs (or two windows side by side).
3. Click Connect in both, using the same room name (the default is lab).
4. Check that both tabs show the same shared key and fingerprint. 
5. Send messages. Each bubble shows the plaintext and the ciphertext that went over the wire.
6. Look at the terminal. It shows that the server only sees public keys and ciphertext.
7. Click Send tampered. This flips one bit, and the receiver shows an authentication failure.
