from serial import Serial
import asyncio
import json
import time


with Serial(port="COM7", baudrate=115200, timeout=0.1) as arduino:
    
    def send_to_arduino(data: str):
        arduino.write(str(data).encode())

    def read_arduino_response() -> bool:
        # Read from arduino
        for c in arduino.read():
            return c == 49
        return False

    def read_arduino_rfid_response():
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
        # Clear serial
        arduino.readline()

        send_to_arduino(f'0,0,0,0,1')
        while (read_arduino_rfid_response() != True):
            await asyncio.sleep(1)

    # Inputs are floats between 0 and 1 for positions
    async def move_to(basePos: float, armPos: float, zPos: float, vacuum: int):
        base = -int((1200 + 1200) * basePos - 1200)
        arm = -int((1400 + 1400) * armPos - 1400)
        z = int((14000 + 14000) * zPos - 14000)

        # Send move to arduino
        send_to_arduino(f'{base},{arm},{z},{vacuum},0')

        # Wait for arduino to respond
        while (read_arduino_response() != True):
            await asyncio.sleep(1)

    async def main():
        x = 0.5
        y = 0.5
        z = 0.5
        v = 0
        
        await move_to(x, y, z, v)
        
        while True:
            input_str = input()
            input_str = input_str.lower()

            if input_str == "x":
                x = float(input())
            elif input_str == "y":
                y = float(input())
            elif input_str == "z":
                z = float(input())
            elif input_str == "v":
                v = int(input())
            
            if input_str == "rfid":
                await request_rfid()
            else:
                await move_to(x, y, z, v)

    if __name__ == "__main__":
        print("Start")

        # Clear serial monitor
        arduino.readline()

        # Wait for robot to get done homeing
        while (read_arduino_response() != True):
            time.sleep(0.3)
        print("Done homing")
        
        asyncio.run(main())