// Zero-dependency relay server. It serves the web page and forwards messages
// between the two peers in a room. It only ever sees PUBLIC keys and CIPHERTEXT.
const http = require('http'), fs = require('fs'), path = require('path');
const PORT = process.env.PORT || 3000, PUB = path.join(__dirname, 'public');
const rooms = new Map(); // room -> Map(peerId -> SSE response)
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' };

function relay(room, from, msg) {
  for (const [id, r] of rooms.get(room) || []) if (id !== from) r.write(`data: ${JSON.stringify(msg)}\n\n`);
}

http.createServer((req, res) => {
  const u = new URL(req.url, 'http://localhost');
  const room = u.searchParams.get('room'), id = u.searchParams.get('id');

  if (u.pathname === '/events') {                       // peer opens a live stream
    const peers = rooms.get(room) || new Map();
    if (peers.size >= 2) { res.writeHead(409); return res.end('Room full'); }
    rooms.set(room, peers); peers.set(id, res);
    res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
    res.write('retry: 2000\n\n');
    console.log(`[${room}] ${id} joined (${peers.size}/2)`);
    req.on('close', () => {
      peers.delete(id); if (!peers.size) rooms.delete(room);
      relay(room, id, { type: 'leave' }); console.log(`[${room}] ${id} left`);
    });
    return;
  }
  if (u.pathname === '/send' && req.method === 'POST') { // peer posts a message
    let body = ''; req.on('data', c => body += c);
    req.on('end', () => {
      try {
        const m = JSON.parse(body); relay(room, id, m);
        console.log(`[${room}] server sees from ${id}:`, JSON.stringify(m).slice(0, 120));
        res.writeHead(204); res.end();
      } catch { res.writeHead(400); res.end(); }
    });
    return;
  }
  const file = path.join(PUB, u.pathname === '/' ? 'index.html' : path.normalize(u.pathname));
  if (!file.startsWith(PUB)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (e, d) => {
    if (e) { res.writeHead(404); return res.end('Not found'); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' }); res.end(d);
  });
}).listen(PORT, () => console.log(`Secure chat running -> http://localhost:${PORT}  (open it in TWO tabs)`));
