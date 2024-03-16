import './App.css';
import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import axios from 'axios'; // Make sure to install axios using: npm install axios

const config = path.join(__dirname, "..", "..", "config.json");
const serverIp = require(config).SERVER_IP;

const socket = io(`http://${serverIp}:3000`); // Connect to the server's socket


function App() {
  const [predictionStatus, setPredictionStatus] = useState('off');
  const [pumpSwitchStatus, setPumpSwitchStatus] = useState('off');

  useEffect(() => {
    // Fetch initial state from the server when the component mounts
    fetchInitialState();

    // Listen for initial state from the server
    socket.on('initialState', (initialState) => {
      setPredictionStatus(initialState.predictionStatus);
      setPumpSwitchStatus(initialState.pumpSwitchStatus);
    });

    // Listen for updated state from the server
    socket.on('updatedState', (updatedState) => {
      setPredictionStatus(updatedState.predictionStatus);
      setPumpSwitchStatus(updatedState.pumpSwitchStatus);
    });

    return () => {
      socket.disconnect();
    };

  }, []);

  const fetchInitialState = async () => {
    try {
      const response = await axios.get(`http://${serverIp}:3000/getInitialState`);
      const initialState = response.data;
      setPredictionStatus(initialState.predictionStatus);
      setPumpSwitchStatus(initialState.pumpSwitchStatus);
    } catch (error) {
      console.error('Error fetching initial state:', error);
    }
  };

  const togglePredictionStatus = () => {
    const newStatus = predictionStatus === 'on' ? 'off' : 'on';
    updateServerState({ predictionStatus: newStatus, pumpSwitchStatus });
  };

  const togglePumpSwitchStatus = () => {
    const newStatus = pumpSwitchStatus === 'on' ? 'off' : 'on';
    updateServerState({ predictionStatus, pumpSwitchStatus: newStatus });
  };

  const updateServerState = async (newState) => {
    try {
      // Update the local state after a successful request
      setPredictionStatus(newState.predictionStatus);
      setPumpSwitchStatus(newState.pumpSwitchStatus);
      socket.emit('updateState', newState);
      console.log('Server State Update Attempted');
    } catch (error) {
      console.error('Error updating server state:', error);
    }
  };

  const getStatusColor = (status) => {
    return status === 'on' ? 'var(--on)' : 'var(--off)';
  };

  return (
    <div className="App">
      <div className="Header">
        <p>AquaCirc</p>
      </div>
      <div className="Controls">
        <div className="Prediction" onClick={togglePredictionStatus} style={{ backgroundColor: getStatusColor(predictionStatus) }}>
          <p>Prediction</p>
          <p>Turn Off</p>
        </div>
        <div className="PumpSwitch" onClick={togglePumpSwitchStatus} style={{ backgroundColor: getStatusColor(pumpSwitchStatus) }}>
          <p>Pump Switch</p>
          <p>Turn On</p>
        </div>
      </div>
    </div>
  );
}


export default App;
