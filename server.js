const http = require('http');
const fs = require('fs');
const path = require('path');
const socketIO = require('socket.io'); 
const config = path.join(__dirname, "config.json");
const httpPort = require(config).WEB_SOCKET_PORT;

// State variables
let predictionStatus = 'off';
let pumpSwitchStatus = 'off';

// HTTP server
const httpServer = http.createServer((req, res) => {
  // Serve static files from the 'build' folder for HTTP requests
  console.log(req.url);
  if (req.method === 'GET') {
    if (req.url === '/') {
      const filePath = path.join(__dirname, 'frontend', 'build', 'index.html');
      serveStaticFile(filePath, res);
    } else if (req.url === '/getInitialState') {
      // Respond with the current state when the client requests the initial state
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ predictionStatus, pumpSwitchStatus }));
    } else {
      const filePath = path.join(__dirname, '/frontend/build/', req.url);
      serveStaticFile(filePath, res);
    }
  } 
  else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  }
});

const serveStaticFile = (filePath, res) => {
  const extname = path.extname(filePath);
  let contentType = 'text/html';

  switch (extname) {
    case '.js':
      contentType = 'text/javascript';
      break;
    case '.css':
      contentType = 'text/css';
      break;
    case '.json':
      contentType = 'application/json';
      break;
    case '.png':
      contentType = 'image/png';
      break;
    // Add more cases for other file types as needed
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(data);
    }
  });
};


httpServer.listen(httpPort, () => {
  console.log(`HTTP server is listening on port ${httpPort}`);
});

const updateState = (newState) => {
  console.log(`newState: ${newState}`);
  predictionStatus = newState.predictionStatus;
  pumpSwitchStatus = newState.pumpSwitchStatus;
  console.log('Updated state:', { predictionStatus, pumpSwitchStatus });
};

const io = socketIO(httpServer);

io.on('connection', (socket) => {
    console.log('A client connected');
  
    // Send the initial state when a client connects
    socket.emit('initialState', { predictionStatus, pumpSwitchStatus });
  
    // Handle state updates from the client
    socket.on('updateState', (newState) => {
      console.log('Received state update:', newState);
      updateState(newState);
      // Broadcast the updated state to all connected clients
      io.emit('updatedState', { predictionStatus, pumpSwitchStatus });
    });

    // Handle WebSocket messages from Python
    socket.on('pythonUpdate', (pythonState) => {
        console.log('Received state update from Python:', pythonState);
        updateState(pythonState);
        io.emit('updatedState', { predictionStatus, pumpSwitchStatus });
    });

    // Handle WebSocket messages requesting initial state
    socket.on('requestInitialState', () => {
        console.log('Python requested initial state');
        // Send the initial state to Python
        socket.emit('initialState', { predictionStatus, pumpSwitchStatus });
    });
  
    socket.on('disconnect', () => {
      console.log('A client disconnected');
    });
  });

