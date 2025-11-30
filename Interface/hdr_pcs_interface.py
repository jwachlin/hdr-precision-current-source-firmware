import serial
import time 
import struct 
import array
import sys 
import serial.tools.list_ports
import numpy as np

class CURRENT_SETTING:
    def __init__(self, time, stage, current_ma):
        self.time = time 
        self.stage = stage
        self.current_ma = current_ma 

def get_packet(ser, start_time, timeout):
    step = 0
    count = 0
    msg_type = 0
    length = 0
    chk = 0
    payload = []

    while time.time() < start_time + timeout:
        try:
            data = ser.read(1)
        except TypeError:
            return None
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
                print("Checksum wrong. Should be {0}, was {1}".format(chk, data))
                print("Payload: ")
                print(payload)
                step = 0
                count = 0
                payload = []

def display_how_to_use():
    print("To use, follow these rules:")
    print("python hdr_pcs_interface.py h --- Provides helpful information")
    print("python hdr_pcs_interface.py s [scale] --- Set to specific scale if in constant reference mode")
    print("python hdr_pcs_interface.py c [current_setting_mA]  --- Set to specific current if in adjustable reference mode")

if __name__ == "__main__":

    # Figure out the correct port
    port = ""
    connected = [comport for comport in serial.tools.list_ports.comports()]

    for comport in connected:
        if comport.vid == 1155 and comport.pid == 100:
            port = comport[0]
            break

    if port != "":
        ser = serial.Serial(port, timeout=0.1)  # open serial port
        print("Connected to HDR Precision Current Source")
    else:
        print("Could not connect to HDR Precision Current Source")
        sys.exit()

    ser.reset_input_buffer()

    if(len(sys.argv) > 1):
        command_character = sys.argv[1]
        if command_character == 's':
            print("Stage command")
            if len(sys.argv) > 2:
                stage = int(sys.argv[2])
            else:
                print("With scale command, please provide a scale")
                display_how_to_use()
                exit()

            # Assemble command and send
            payload = [0xAA,0x04,1,stage]

            chk = 0
            for i in range(1,len(payload)):
                chk += payload[i]
                chk &= 0xFF
            payload.append(chk)
            ser.write(bytearray(payload))

            (msg_type, length, payload) = get_packet(ser, time.time(), 0.5)
            if(msg_type == 5 and length == 4):
                # CURRENT_SET 
                current_set_mA = struct.unpack('<f', bytes(payload))[0]
                print("At stage {0}, current setting is {1:.6f} mA".format(stage, current_set_mA))

        elif command_character == 'c':
            print("Current command")
            if len(sys.argv) > 2:
                current_cmd_mA = float(sys.argv[2])
            else:
                print("With current command, please provide a current in mA")
                display_how_to_use()
                exit()

            # Assemble command and send
            payload = [0xAA,0x00,4]
            payload.extend(struct.pack('<f', current_cmd_mA))

            chk = 0
            for i in range(1,len(payload)):
                chk += payload[i]
                chk &= 0xFF
            payload.append(chk)
            ser.write(bytearray(payload))

            (msg_type, length, payload) = get_packet(ser, time.time(), 0.5)
            if(msg_type == 5 and length == 4):
                # CURRENT_SET 
                current_set_mA = struct.unpack('<f', bytes(payload))[0]
                print("Current commanded {0:.6f} mA, current setting is {1:.6f} mA".format(current_cmd_mA, current_set_mA))

            
        elif command_character == 'h':
            display_how_to_use()
            exit()
    else:
        print("Incorrect inputs. Please follow the instructions below.")
        print("..........")
        display_how_to_use()
        exit()

    ser.close()