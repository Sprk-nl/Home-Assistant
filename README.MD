"hass-visonic-mqtt" is a Toolkit to connect a Visonic alarm via rfxtrx on 868 Mhz through mqtt to Home Assistant.
Home Assistant was at this time not stable and/or could not work with multiple rfx radio's.
This is a quick and dirty script to get the job done.

The user that runs the script needs access to the "dialout" group.

> $ cat /etc/group | grep dialout
> dialout:x:20:pi

The script connects to the rfxcom and passes data to a localhost mqtt broker
Check in the code if your rfxcom is also connected to the correct /dev/tty device

The script sends data with a json layout.

Message Payload : b'{"battery": "9", "status": "No Motion", "rssi": "8"}'
Message Topic   : homeassistant/visonic/1099C9

Run the python script in background via:

> $ nohup /home/homeassistant/.homeassistant/mqtt/rfxtrx868_visonic.py &
