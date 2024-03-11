# Set up

Make sure nodejs is already installed in your pi

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
YOu will need to play around with the value of channel

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













