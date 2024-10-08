# Smart Hot Water Recirculation System

The Smart Hot Water Recirculation System is an IoT-based solution designed to address the inconvenience and energy inefficiencies of conventional hot water recirculation systems. It leverages predictive algorithms to provide instant hot water while minimizing energy costs by reducing unnecessary pump usage.

## Authors
- Roshan Sevalia
- Kyle Mondina
- Lakshmi Priya
- Xavier Kuehn

This project was completed as part of COEN 243 - Internet of Things at Santa Clara University under the guidance of Professor Yen-Kuang Chen
## Implementation Overview
   ![SoftwareArchitectureOverview](/SoftwareArchitectureOverview.PNG)

### Controller
The controller component of our IoT system is comprised of `main.py`, which operates with two concurrent running thread functions. The prediction thread executes once daily as specified in `config.json`. It utilizes the prediction algorithm, which reads data from the `running_data.csv` file and generates `hw_forecast.csv` for the current day's predicted hot water usage. The pump switch thread then interprets this data and adjusts the pump's status accordingly. Additionally, `main.py` shares state information with `server.js`. The prediction thread's target function is set to the arima function defined in main.py in this current configuration. 

`Server.js` operates as a concurrent process, hosting the UI webpages and providing real-time updates on the prediction services and pump status for user monitoring and control. Any alterations to these state variables are communicated to pump.py via Socket.IO, where main.py establishes a connection with `server.js`.

### Sensing
`accel_processor.py` handles the interface and processing of the accelerometer for sensing water flow. It contains functions for interfacing with the sensor over I2C, a producer process, and a consumer process. The producer process opens a connection to the sensor and collects samples at 1kHz into an array and sends them to the consumer using a cross-process queue. it also runs a self test of the sensors and monitors the temperature of the sensor to shut it down if it exceeds the operating threshold of the sensor. The consumer listens for new pushes to that queue, pops the sample segments, then executes a fast fourier transform to shift the signal into the frequency domain for analysis as described in the report document. State changes are recorded into the `running-data.csv` file where they can be read by the prediction system. Details about the individual sensor interface functions are mentioned in the file's comments.

### Deep Learning
The files pertaining to the deep learning approach are called `seq_forecast.py` and `seq-data.csv`. The former contains class definintions for the model, helper functions and the main `run` function. This is the function that is called by the controller in place of `predict_by_arima`. The `run` function has three modes: training, evalutation, and forecasting. In the case that the deep learning is rolled out only once enough data is collected by the system, the controller would first train the model (via `run(mode='train')`), evaluate it (via `run(mode='eval')`), and finally forecast (via `run(historical_data, mode='forecast')`) where the historical data is simply historical hot water usage data stored by the system. When `run` is called in forecast mode, it returns a list of 96 values (0 or 1) corresponding to whether hot water will be needed at each timestep for the following day. This list will be added to `hw_forecast.csv`. `seq-data.csv` is the augmented data used to train the model and should be refined for production use cases.

## Set up

Make sure nodejs is already installed in your pi

### Set up neccessary config variable

In config.json set the appropriate config variables

```json
	"HW_LED_PIN": "The LED pin number you are connecting to indicate pump status"
	"PUMP_SWITCH_INTV": "Interval in minutes of how often you want the pi to check if hot water is needed"
	"PREDICTION_SCHEDULE": "Time of day you want the prediction algorithm to run"
	"SERVER_IP": "IP of the gateway that you set to connect to the UI frontend, default should be 192.168.4.1"
	"WEB_SOCKET_PORT": "Port of server you will be hosting the UI, default is 3000"
	"HOT_WATER_HISTORY_FILE": "CSV file where you store hot water demand history",
	"HOT_WATER_FORECAST_FILE": "CSV file where you store hot water demand forecast"
```

### Build React Client and Nodejs Server

1. Download necessary nodejs modules for server.js

```bash

npm install
```

2. Download necessary nodejs modules for React.js client and build React.js client

```bash

cd frontend
npm install
npm run build
```

### Install ncessary python modules for main.py

```bash

pip install python-socketio
pip install gpiozero
```

### Set up Rasbery Pi as a wifi access point

1. Install the necessary packages for setting up the access point:

```bash

sudo apt install dnsmasq hostapd

```

2. Configure a Static IP Address:
```bash

sudo nano /etc/dhcpcd.conf
```

3. Add the following lines at the end of the file:
```bash

interface wlan0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
```
4. Configure dnsmasq to provide DHCP and DNS services:

```bash

sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```

5. Add the following lines to the file:

```bash

interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
```

6. Configure hostapd for the access point:

```bash

sudo nano /etc/hostapd/hostapd.conf
```

7. Add the following configuration:

```bash

interface=wlan0
ssid=IOTWinter24
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=IOTWinter24
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```
You will need to play around with the value of channel

8. Tell hostapd where to find the configuration:
```bash
sudo nano /etc/default/hostapd
```

9. Find the line #DAEMON_CONF="" and replace it with:
```bash
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

10. Enable and start the services:
```bash
sudo systemctl start hostapd
sudo systemctl start dnsmasq
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
```

### Start the server.js and main.py
```bash
node server.js
python main.py
```


### Connect to pi
1. Connect to wifi IOTWinter24, password same as name

2. To access UI, go to:
```bash
http://192.168.4.1:3000
```

## Running
To run, cd to the main folder of the repository and run `./run.sh`. Check the outputs folder for stdout dumps of each process. To stop running, kill the 3 PIDs in the run.pid file.
