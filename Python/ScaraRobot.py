#        0     <->  1
# Base   1200  <-> -1200
# Arm    1400  <-> -1400
# Z     -14000 <->  14000

from nats.aio.client import Client as NATS
from serial import Serial
import asyncio
import json
import time


with Serial(port="COM7", baudrate=115200, timeout=0.1) as arduino:
    
    def clear_serial():
        arduino.readline()

    def send_to_arduino(data: str):
        arduino.write(str(data).encode())

    def read_arduino_response() -> bool:
        # Read from arduino
        for c in arduino.read():
            return c == 49
        return False
    
    def read_arduino_rfid_response():
        global rfid
        # Read from arduino
        response = arduino.readline()

        if (response != b''):
            print("Recived rfid")
            rfid = str(response)
            rfid = rfid.lstrip("b")
            rfid = rfid.strip("'")
            rfid = rfid.rstrip("\\r\\n")
            print(rfid)
            return True

        return False

    # The robot should be positioned over the rfid reader when this is called
    async def request_rfid():
        clear_serial()
        send_to_arduino(f'0,0,0,0,1')
        while (read_arduino_rfid_response() != True):
            await asyncio.sleep(0.1)
    
    async def manuel_homing():
        clear_serial()
        send_to_arduino(f'0,0,0,0,2')

        print("Homeing...")
        # Wait for robot to get done homeing
        while (read_arduino_response() != True):
            time.sleep(0.3)
        print("Done homing")

    # Inputs are floats between 0 and 1 for positions
    async def move_to(basePos: float, armPos: float, zPos: float, vacuum: int):
        base = -int((1200 + 1200) * basePos - 1200)
        arm = -int((1400 + 1400) * armPos - 1400)
        z = int((14000 + 14000) * zPos - 14000)

        clear_serial()

        # Send move to arduino
        send_to_arduino(f'{base},{arm},{z},{vacuum},0')

        # Wait for arduino to respond
        while (read_arduino_response() != True):
            await asyncio.sleep(0.1)

    async def main():
        nc = NATS()

        print("Connecting to server..")
        await nc.connect(
            servers=["tls://nats.eupronet.hu:4222"],
            user="norway",
            password="V7711TqZNPvDnd07wC6tiQ"
        )

        if (nc.is_connected):
            print("Successfuly conncted to server")
        else:
            print("Failed to conncted to server")

        async def message_handler(msg):
            subject = msg.subject
            reply = msg.reply
            data = msg.data.decode()

            jsonData = json.loads(data)

            if (jsonData["code"] == 301):
                print("Start moving")
                await run_robot()
                print("Done moving")

                print("Publishing finish message to server")
                
                payload = {
                    "code": 303,
                    "payload": {
                        "rfid": rfid
                    }
                }
                payload_str = json.dumps(payload)
                print("Payload", payload_str)

                await nc.publish("rfidarm.telemetry", payload_str.encode())
                print("Done publishing")
                
        sub = await nc.subscribe("rfidarm.job", cb=message_handler)

        # TEST
        # await request_rfid()
        # print(rfid)
        # payload = {
        #     "code": 303,
        #     "payload": {
        #         "rfid": rfid
        #     }
        # }
        # payload_str = json.dumps(payload)
        # print("Payload", payload_str)

        while True:
            await run_robot()
            await asyncio.sleep(1)
        
        await sub.drain()
        await nc.drain()
    
    async def run_robot():
        print("Move to above pickup")
        await move_to(1, 0.5, 0.7, 0)
        print("Move down to pickup")
        await move_to(1, 0.5, 0.56, 0)
        print("Turn on vacuum")
        await move_to(1, 0.5, 0.56, 1)
        await asyncio.sleep(1)
        print("Lift up over pickup")
        await move_to(1, 0.5, 0.7, 1)

        print("Move to above rfid reader")
        await move_to(0.01, 0.23, 0.7, 1)
        await move_to(0.01, 0.23, 0.55, 1)
        print("Read the rfid")
        await request_rfid()

        print("Move to drop-off")
        await move_to(0.1, 0.5, 0.55, 1)
        await move_to(0.1, 0.5, 0.27, 1)
        print("Drop chip")
        await move_to(0.1, 0.5, 0.27, 0)
        await asyncio.sleep(1)

        await move_to(0.1, 0.5, 0.5, 0)

        await manuel_homing()

    if __name__ == "__main__":
        print("Start")

        clear_serial()

        print("Homeing...")
        # Wait for robot to get done homeing
        while (read_arduino_response() != True):
            time.sleep(0.3)
        print("Done homing")
        
        asyncio.run(main())
