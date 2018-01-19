A Toolkit to connect the rfxtrx on 868 Mhz for Visonic alarm systems to Home Assistant.
As Home Assistant was not as stable and/or could not work with multiple rfx radio's, I made a mqtt script.

The script connects to the rfxcom and passes data to a localhost mqtt broker
Sending data as:

Message Payload : b'{"battery": "9", "status": "No Motion", "rssi": "8"}'
Message Topic   : homeassistant/visonic/1099C9

Home Assistant config:
mqtt:
  broker: 127.0.0.1
  discovery: true
  discovery_prefix: homeassistant

Sensors:
- platform: mqtt
  state_topic: "homeassistant/visonic/1099C9"
  name: "STATUS_PIR_Bijkeuken"
  #unit_of_measurement: "%"
  value_template: '{{ value_json.status }}'
- platform: mqtt
  state_topic: "homeassistant/visonic/1099C9"
  name: "BATT_PIR_Bijkeuken"
  #unit_of_measurement: "%"
  value_template: '{{ value_json.battery }}'
- platform: mqtt
  state_topic: "homeassistant/visonic/1099C9"
  name: "RSSI_PIR_Bijkeuken"
  #unit_of_measurement: "%"
  value_template: '{{ value_json.rssi }}'

groups:
visonic_status:
  view: no
  name: visonic_status
  entities:
    - sensor."STATUS_PIR_Bijkeuken"
