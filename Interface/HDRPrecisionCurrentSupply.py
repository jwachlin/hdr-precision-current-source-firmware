
import serial
import time 
import struct 
import serial.tools.list_ports
from enum import Enum

class CurrentSupplyType(Enum):
    FIXED_REFERENCE = 1
    ADJUSTABLE_REFERENCE = 2

class HDRPrecisionCurrentSupply:
    def __init__(self, supply_type : CurrentSupplyType):
        self.supply_type = supply_type
        self.ser = None

    def get_packet(self, start_time, timeout):
        step = 0
        count = 0
        msg_type = 0
        length = 0
        chk = 0
        payload = []

        while time.time() < start_time + timeout:
            try:
                data = self.ser.read(1)
            except TypeError:
                return (None, None, None)
            if data:
                data = ord(data)

            if(step == 0 and data == 0xAA):
                step += 1
                chk = 0
            elif(step == 1):
                msg_type = data
                step += 1
                chk += data
                chk &= 0xFF
            elif(step == 2):
                length = data 
                step += 1
                chk += data
                chk &= 0xFF
            elif(step == 3):
                if(count < length):
                    payload.append(data)
                    count += 1
                    chk += data
                    chk &= 0xFF
                    if count == length:
                        step += 1
            elif(step == 4):
                if(data == chk):
                    return (msg_type, length, payload)
                else:
                    print("HDR Current Supply checksum wrong. Should be {0}, was {1}".format(chk, data))
                    print("Payload: ")
                    print(payload)
                    step = 0
                    count = 0
                    payload = []
        return (None, None, None)
    
    def connect(self):
        # Figure out the correct port
        port = ""
        connected = [comport for comport in serial.tools.list_ports.comports()]

        for comport in connected:
            if comport.vid == 1155 and comport.pid == 100:
                port = comport[0]
                break

        if port != "":
            self.ser = serial.Serial(port, timeout=0.1)  # open serial port
            self.ser.reset_input_buffer()
            print("Connected to HDR Precision Current Source")
            return True
        else:
            print("Could not connect to HDR Precision Current Source")
            return False
        
    def command_stage(self, stage):
        if self.supply_type == CurrentSupplyType.ADJUSTABLE_REFERENCE:
            print("ERROR: In adjustable reference mode. Please command current directly")
            return

        # Assemble command and send
        payload = [0xAA,0x04,1,stage]

        chk = 0
        for i in range(1,len(payload)):
            chk += payload[i]
            chk &= 0xFF
        payload.append(chk)
        self.ser.write(bytearray(payload))

    def command_current_ma(self, current_cmd_ma):
        if self.supply_type == CurrentSupplyType.FIXED_REFERENCE:
            print("ERROR: In fixed reference mode. Cannot command current directly")
            return

        payload = [0xAA,0x00,4]
        payload.extend(struct.pack('<f', current_cmd_ma))

        chk = 0
        for i in range(1,len(payload)):
            chk += payload[i]
            chk &= 0xFF
        payload.append(chk)
        self.ser.write(bytearray(payload))

    def get_current_setting_ma(self):
        (msg_type, length, payload) = self.get_packet(time.time(), 0.5)
        if(msg_type is not None and length is not None):
            if(msg_type == 5 and length == 4):
                # CURRENT_SET 
                current_set_mA = struct.unpack('<f', bytes(payload))[0]
                return current_set_mA
        else:
            return None
        
    def disconnect(self):
        self.ser.close()