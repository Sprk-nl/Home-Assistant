#!/usr/bin/python3
"""
Module documentation.
"""

import paho.mqtt.client as mqtt #import the client1
import json

broker_address="127.0.0.1" 
client = mqtt.Client("P1") #create new instance
client.connect(broker_address) #connect to broker

message_payload = {}
message_payload['status'] = 'No Motion'
message_payload['RSSI'] = 6
message_payload['battery'] = 9

json_data = json.dumps(message_payload)
print (json_data)

client.publish("homeassistant/visonic/10C9C7",json_data)   #publish
