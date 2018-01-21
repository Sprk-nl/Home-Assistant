#!/usr/bin/python3
"""
Module documentation.
"""

from asyncio import get_event_loop
from rfxcom.transport import AsyncioTransport
import sys, errno
import paho.mqtt.client as mqtt #import the client1
from signal import signal, SIGPIPE, SIG_DFL 
import json

# Make sure the following settings are correct and you have access to serial.
broker_address ="127.0.0.1" 
dev_name       = '/dev/ttyUSB1'



client = mqtt.Client("rfxtrx868") #create new instance

# Ignore SIG_PIPE and don't throw exceptions on it... 
# Source: (http://docs.python.org/library/signal.html)
#signal(SIGPIPE,SIG_DFL) 

   

loop = get_event_loop()


 ###############################################################################
# Packet class
###############################################################################

class Packet(object):
    """ Abstract superclass for all low level packets """

    _UNKNOWN_TYPE = "Unknown type ({0:#04x}/{1:#04x})"
    _UNKNOWN_CMND = "Unknown command ({0:#04x})"

    def __init__(self):
        """Constructor"""
        self.data = None
        self.packetlength = None
        self.packettype = None
        self.subtype = None
        self.seqnbr = None
        self.rssi = None
        self.rssi_byte = None
        self.type_string = None
        self.id_string = None

    def has_value(self, datatype):
        """Return True if the sensor supports the given data type.
        sensor.has_value(RFXCOM_TEMPERATURE) is identical to calling
        sensor.has_temperature().
        """
        return hasattr(self, datatype)

    def value(self, datatype):
        """Return the :class:`SensorValue` for the given data type.
        sensor.value(RFXCOM_TEMPERATURE) is identical to calling
        sensor.temperature().
        """
        return getattr(self, datatype, None)

    def __getattr__(self, name):
        typename = name.replace("has_", "", 1)
        if not name == typename:
            return lambda: self.has_value(typename)
        raise AttributeError(name)

    def __eq__(self, other):
        if not isinstance(other, Packet):
            return False
        return self.id_string == other.id_string

    def __str__(self):
        return self.id_string

    def __repr__(self):
        return self.__str__()


###############################################################################
# Status class
###############################################################################

def _decode_flags(data, words):
    """Decode flags """
    words = words.split()
    res = set()
    for word in words:
        if data % 2:
            res.add(word)
        data //= 2
    return res


class Status(Packet):
    """
    Data class for the Status packet type
    """

    TYPES = {
        0x50: '310MHz',
        0x51: '315MHz',
        0x53: '433.92MHz',
        0x55: '868.00MHz',
        0x56: '868.00MHz FSK',
        0x57: '868.30MHz',
        0x58: '868.30MHz FSK',
        0x59: '868.35MHz',
        0x5A: '868.35MHz FSK',
        0x5B: '868.95MHz'
    }
    """
    Mapping of numeric subtype values to strings, used in type_string
    """

    def __str__(self):
        return ("Status [subtype={0}, firmware={1}, devices={2}]") \
            .format(self.type_string, self.firmware_version, self.devices)

    def __init__(self):
        """Constructor"""
        super(Status, self).__init__()
        self.tranceiver_type = None
        self.firmware_version = None
        self.devices = None

    def load_receive(self, data):
        """Load data from a bytearray"""
        self.data = data
        self.packetlength = data[0]
        self.packettype = data[1]

        self.tranceiver_type = data[5]
        self.firmware_version = data[6]

        devs = set()
        devs.update(_decode_flags(data[7] / 0x80,
                                  'undecoded'))
        devs.update(_decode_flags(data[8],
                                  'mertik lightwarerf hideki' +
                                  ' lacrosse fs20 proguard'))
        devs.update(_decode_flags(data[9],
                                  'x10 arc ac homeeasy ikeakoppla' +
                                  ' oregon ati visonic'))
        self.devices = sorted(devs)

        self._set_strings()

    def _set_strings(self):
        """Translate loaded numeric values into convenience strings"""
        if self.tranceiver_type in self.TYPES:
            self.type_string = self.TYPES[self.tranceiver_type]
        else:
            # Degrade nicely for yet unknown subtypes
            self.type_string = 'Unknown'
            

###############################################################################
# SensorPacket class
###############################################################################

class SensorPacket(Packet):
    """
    Abstract superclass for all sensor related packets
    """

    HUMIDITY_TYPES = {0x00: 'dry',
                      0x01: 'comfort',
                      0x02: 'normal',
                      0x03: 'wet',
                      -1: 'unknown humidity'}
    """
    Mapping of humidity types to string
    """

    FORECAST_TYPES = {0x00: 'no forecast available',
                      0x01: 'sunny',
                      0x02: 'partly cloudy',
                      0x03: 'cloudy',
                      0x04: 'rain',
                      -1: 'unknown forecast'}
    """
    Mapping of forecast types to string
    """



###############################################################################
# Security1 class
###############################################################################
class Security1(SensorPacket):
    """
    Data class for the Security1 packet type
    """

    TYPES = {0x00: 'X10 Security',
             0x01: 'X10 Security Motion Detector',
             0x02: 'X10 Security Remote',
             0x03: 'KD101 Smoke Detector',
             0x04: 'Visonic Powercode Door/Window Sensor Primary Contact',
             0x05: 'Visonic Powercode Motion Detector',
             0x06: 'Visonic Codesecure',
             0x07: 'Visonic Powercode Door/Window Sensor Auxilary Contact',
             0x08: 'Meiantech',
             0x09: 'Alecto SA30 Smoke Detector'}
    """
    Mapping of numeric subtype values to strings, used in type_string
    """
    STATUS = {0x00: 'Normal',
              0x01: 'Normal Delayed',
              0x02: 'Alarm',
              0x03: 'Alarm Delayed',
              0x04: 'Motion',
              0x05: 'No Motion',
              0x06: 'Panic',
              0x07: 'End Panic',
              0x08: 'IR',
              0x09: 'Arm Away',
              0x0A: 'Arm Away Delayed',
              0x0B: 'Arm Home',
              0x0C: 'Arm Home Delayed',
              0x0D: 'Disarm',
              0x10: 'Light 1 Off',
              0x11: 'Light 1 On',
              0x12: 'Light 2 Off',
              0x13: 'Light 2 On',
              0x14: 'Dark Detected',
              0x15: 'Light Detected',
              0x16: 'Battery low',
              0x17: 'Pairing KD101',
              0x80: 'Normal Tamper',
              0x81: 'Normal Delayed Tamper',
              0x82: 'Alarm Tamper',
              0x83: 'Alarm Delayed Tamper',
              0x84: 'Motion Tamper',
              0x85: 'No Motion Tamper'}
    """
    Mapping of numeric status values to strings, used in type_string
    """

    def __str__(self):
        # originally it starts with: return ("Security1 [subtype={0
        # I modified it, because I needed a usable list as output
        return ("[subtype={0}, seqnbr={1}, id={2}, status={3}, " +
                "battery={4}, rssi={5}]") \
            .format(self.type_string, self.seqnbr, self.id_string,
                    self.security1_status_string, self.battery, self.rssi)

    def __init__(self):
        """Constructor"""
        super(Security1, self).__init__()
        self.id1 = None
        self.id2 = None
        self.id3 = None
        self.id_combined = None
        self.security1_status = None
        self.battery = None
        self.rssi = None
        self.security1_status_string = 'unknown'

    def load_receive(self, data):
        """Load data from a bytearray"""
        self.data = data
        self.packetlength = data[0]
        self.packettype = data[1]
        self.subtype = data[2]
        self.seqnbr = data[3]
        self.id1 = data[4]
        self.id2 = data[5]
        self.id3 = data[6]
        self.id_combined = (self.id1 << 16) + (self.id2 << 8) + self.id3
        self.security1_status = data[7]
        self.rssi_byte = data[8]
        self.battery = self.rssi_byte & 0x0f
        self.rssi = self.rssi_byte >> 4
        self._set_strings()

    def _set_strings(self):
        """Translate loaded numeric values into convenience strings"""
        self.id_string = "{0:06x}:{1}".format(self.id_combined, self.packettype)
        if self.subtype in self.TYPES:
            self.type_string = self.TYPES[self.subtype]
        else:
            # Degrade nicely for yet unknown subtypes
            self.type_string = self._UNKNOWN_TYPE.format(self.packettype,
                                                         self.subtype)
        if self.security1_status in self.STATUS:
            self.security1_status_string = self.STATUS[self.security1_status]

###############################################################################
# Rfy class
###############################################################################


class Rfy(Packet):
    """
    Data class for the Rfy packet type
    """
    TYPES = {0x00: 'Rfy',
             0x01: 'Rfy Extended',
             0x03: 'ASA'}
    """
    Mapping of numeric subtype values to strings, used in type_string
    """

    COMMANDS = {0x00: 'Stop',
                0x01: 'Up',
                0x03: 'Down'}
    """
    Mapping of command numeric values to strings, used for cmnd_string
    """

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Rfy [subtype={0}, seqnbr={1}, id={2}, cmnd={3}]" \
            .format(
                self.subtype,
                self.seqnbr,
                self.id_string,
                self.cmnd_string
            )

    def __init__(self):
        """Constructor"""
        super(Rfy, self).__init__()
        self.id1 = None
        self.id2 = None
        self.id3 = None
        self.id_combined = None
        self.unitcode = None
        self.cmnd = None
        self.cmnd_string = None

    def parse_id(self, subtype, id_string):
        """( a string id into individual components"""
        try:
            self.packettype = 0x1a
            self.subtype = subtype
            self.id_combined = int(id_string[:6], 16)
            self.id1 = self.id_combined >> 16
            self.id2 = self.id_combined >> 8 & 0xff
            self.id3 = self.id_combined & 0xff
            self.unitcode = int(id_string[7:])
            self._set_strings()
        except:
            raise ValueError("Invalid id_string")
        if self.id_string != id_string:
            raise ValueError("Invalid id_string")

    def load_receive(self, data):
        """Load data from a bytearray"""
        self.data = data
        self.packetlength = data[0]
        self.packettype = data[1]
        self.subtype = data[2]
        self.seqnbr = data[3]
        self.id1 = data[4]
        self.id2 = data[5]
        self.id3 = data[6]
        self.unitcode = data[7]
        if self.packetlength > 7:
            self.cmnd = data[8]

        self.id_combined = (self.id1 << 16) + (self.id2 << 8) + self.id3
        self._set_strings()

    def set_transmit(self, subtype, seqnbr, id_combined, unitcode, cmnd):
        """Load data from individual data fields"""
        self.packetlength = 0x08
        self.packettype = 0x1a
        self.subtype = subtype
        self.seqnbr = seqnbr
        self.id_combined = id_combined
        self.id1 = id_combined >> 16
        self.id2 = id_combined >> 8 & 0xff
        self.id3 = id_combined & 0xff
        self.unitcode = unitcode
        self.cmnd = cmnd
        self.data = bytearray([self.packetlength, self.packettype,
                               self.subtype, self.seqnbr,
                               self.id1, self.id2, self.id3, self.unitcode,
                               self.cmnd])

        self._set_strings()

    def _set_strings(self):
        """Translate loaded numeric values into convenience strings"""
        self.id_string = "{0:06x}:{1}".format(self.id_combined,
                                              self.unitcode)

        if self.subtype in self.TYPES:
            self.type_string = self.TYPES[self.subtype]
        else:
            # Degrade nicely for yet unknown subtypes
            self.type_string = self._UNKNOWN_TYPE.format(self.packettype,
                                                         self.subtype)

        if self.cmnd is not None:
            if self.cmnd in self.COMMANDS:
                self.cmnd_string = self.COMMANDS[self.cmnd]
            else:
                self.cmnd_string = self._UNKNOWN_CMND.format(self.cmnd)
  
def mqqt_send_message_test():
    message_payload = {}
    message_payload['status'] = 'No Motion'
    message_payload['rssi'] = 6
    message_payload['battery'] = 9
    
    try:
        client.connect(broker_address) #connect to broker
        #print('Connected to mqtt broker')
        json_data = json.dumps(message_payload)
        #print (json_data)
        client.publish("homeassistant/visonic/10FFFF",json_data)   #publish
    except:
        print("Connection failed to MQTT broker")

def mqtt_send_message(visonic_id, content):
    #print('sending mqtt message:')
    msg_topic   = 'homeassistant/visonic/' + str(visonic_id).upper()
    msg_payload = content

    try:
        client.connect(broker_address) #connect to broker
        #print('Connected to mqtt broker')
    except:
        print("Connection failed to MQTT broker")
        

    try:     
        #publish to mqtt broker
        #print('msg_topic   : {}'.format(str(msg_topic)))
        #print('msg_payload : {}'.format(str(msg_payload)))
        client.publish(msg_topic, str(msg_payload))        
    except:
        print('sending mqtt ERROR!')


def handler(packet):
    packet_list = []
    # #print out the packet - the string representation will show us the type.
    #print(packet)

    # Each packet will have a dictionary which contains parsed data.
    if 'packet' in packet.data:
        data = packet.data['packet']

    # You can access the raw bytes from the packet too.
    #print(packet.raw)

    try:
        if 'packet' in packet.data: # Has it data in packet
            data = packet.data['packet']
            if data[1] == 0x20: #is it Visonic?
                pkt = Security1()
                pkt.load_receive(data) #Convert hex data to reable text
                # #print the packet as it is processed by the code from HASS:
                # The #printed output looks like: [subtype=Visonic Powercode Motion Detector, seqnbr=1, id=10c9c7:32, status=No Motion, battery=9, rssi=8]
                #print(pkt)

                # Define the topic and payload elements before sending via mqtt:
                visonic_id     = str(format(pkt.id_combined, '06x'))           
                message_payload = {}
                message_payload['status'] = str(format(pkt.security1_status_string))
                message_payload['rssi'] = str(format(pkt.rssi))
                message_payload['battery'] = str(format(pkt.battery))

                #Change the python dict layout to json
                message_payload_json = json.dumps(message_payload)
               
                #Call the mqqt 
                mqtt_send_message(visonic_id, message_payload_json)
                #use the test message below to send out a test call
                #mqqt_send_message_test()
    except Exception as e:
        print("type error: " + str(e))
        print(traceback.format_exc())
    except IOError as e:
        print ("I/O error({0}): {1}".format(e.errno, e.strerror))
    except ValueError:
        print ("Could not convert data to an integer.")
    except:
        print('ERROR in function handler')
        print ("Unexpected error:", sys.exc_info()[0])
        raise

        
try:
    #print('Started rfxcom communication')
    rfxcom = AsyncioTransport(dev_name, loop, callback=handler)
    loop.run_forever()
finally:
    loop.close()
