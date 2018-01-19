A Toolkit to connect the rfxtrx on 868 Mhz for Visonic alarm systems to Home Assistant.
As Home Assistant was not as stable and/or could not work with multiple rfx radio's, I made a mqtt script.

The script connects to the rfxcom and passes data to a localhost mqtt broker
Sending data as:

Message Payload : b'{"battery": "9", "status": "No Motion", "rssi": "8"}'
Message Topic   : homeassistant/visonic/1099C9

