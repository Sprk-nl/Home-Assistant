# What is rfxtrx868_mqtt_hass
It's a Python3 Toolkit to:
- receive Visonic data via the rfxtrx (868 Mhz)
- translate packets to readable text
- send to mqtt broker
- use them in  Home Assistant.

# Why?
Home Assistant was at this time not stable and/or could not work with multiple rfx radio's.
This is a quick and dirty script to get the job done.

# HOW
The user that runs the script needs access to the "dialout" group.

```
cat /etc/group | grep dialout
dialout:x:20:pi
```

Check rfxtrx868_mqtt_hass.py for correct mqtt broker and serial port

```
broker_address = '127.0.0.1'
dev_name       = '/dev/ttyUSB1'
```

The script sends data with a json layout.

```
Message Payload : b'{"battery": "9", "status": "No Motion", "rssi": "8"}'
Message Topic   : homeassistant/visonic/1099C9

```
Run the python script in background via:

```
nohup /home/homeassistant/.homeassistant/mqtt/rfxtrx868_visonic.py &
```

Note:
Python classes: Packet, Status, SensorPacket, Security1 and Rfy
are copied from home-assistant to keep maximum message compatibility.