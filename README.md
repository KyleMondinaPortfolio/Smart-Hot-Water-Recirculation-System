# Set up

Make sure nodejs is already installed in your pi

## Set up neccessary config variable

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

## Build React Client and Nodejs Server

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

## Install ncessary python modules for main.py

```bash

pip install python-socketio
pip install gpiozero
```

## Set up Rasbery Pi as a wifi access point

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

## Start the server.js and main.py
```bash
node server.js
python main.py
```


## Connect to pi
1. Connect to wifi IOTWinter24, password same as name

2. To access UI, go to:
```bash
http://192.168.4.1:3000
```

# Running
To run, cd to the main folder of the repository and run `./run.sh`. Check the outputs folder for stdout dumps of each process. To stop running, kill the 3 PIDs in the run.pid file.
