#include <SPI.h>
#include <MFRC522.h>

#include <AccelStepper.h>
#include <Servo.h>
#include <math.h>

// IO
#define limitSwitchBase 11
#define limitSwitchArm 10
#define limitSwitchZ A3
#define vacuum 12

AccelStepper stepperBase(1, 2, 5); // (Type:driver, STEP, DIR)
AccelStepper stepperArm(1, 3, 6);
AccelStepper stepperZ(1, 4, 7);

// RFID
MFRC522 rfid(53, 46); // (SS, Reset) 

int data[5];
/*
    data[0] - BasePos
    data[1] - ArmPos
    data[2] - ZPos
    data[3] - Vacuum
    data[4] - ReadRFID
*/

void setup()
{
    Serial.begin(115200);

    // RFID
    SPI.begin();
    rfid.PCD_Init();

    pinMode(limitSwitchBase, INPUT_PULLUP);
    pinMode(limitSwitchArm, INPUT_PULLUP);
    pinMode(limitSwitchZ, INPUT_PULLUP);
    pinMode(vacuum, OUTPUT);

    stepperBase.setMaxSpeed(4000);
    stepperBase.setAcceleration(2000);
    stepperArm.setMaxSpeed(2000);
    stepperArm.setAcceleration(2000);
    stepperZ.setMaxSpeed(2000);
    stepperZ.setAcceleration(2000);
    
    Homing();
    MoveDone();
}

void loop()
{
    // Wait for a command from python
    while (!ReadSerial());

    // If we should read rfid
    if (data[4] == 1)
    {
        while (true)
        {
            if (rfid.PICC_IsNewCardPresent())
            {
                rfid.PICC_ReadCardSerial();

                byte *buffer = rfid.uid.uidByte;
                byte bufferSize = rfid.uid.size;

                String rfid_str;

                // Print to serial monitor
                for (byte i = 0; i < bufferSize; i++)
                {
                    rfid_str += buffer[i] < 0x10 ? "0" : "";
                    rfid_str += int(buffer[i]);
                    if (i < bufferSize - 1)
                        rfid_str += ";";
                }

                // Send back to python
                Serial.println(rfid_str);

                // Halt PICC
                rfid.PICC_HaltA();
                // Stop encrypting on PCD
                rfid.PCD_StopCrypto1();

                break;
            }
            delay(100);
        }
    }
    else {
        // Set vacuume state
        digitalWrite(vacuum, data[3]);

        MoveRobot();

        // Called after the move is done
        MoveDone();
    }
}

void MoveRobot()
{
    // Move stepper Z
    stepperZ.moveTo(data[2]);
    while (stepperZ.currentPosition() != data[2])
    {
        stepperZ.run();
    }

    // Move stepper Arm to start postion
    stepperArm.moveTo(data[1]);
    while (stepperArm.currentPosition() != data[1])
    {
        stepperArm.run();
    }

    // Move stepper Arm to start postion
    stepperBase.moveTo(data[0]);
    while (stepperBase.currentPosition() != data[0])
    {
        stepperBase.run();
    }
}

// Read data from serial
bool ReadSerial()
{
    if (Serial.available())
    {
        String serialContent = Serial.readString();

        for (int i = 0; i < (sizeof(data) / sizeof(data[0])); i++)
        {
            // Locate the first ","
            int index = serialContent.indexOf(",");
            // Extract the number from start to the ","
            data[i] = atol(serialContent.substring(0, index).c_str());
            // Remove the number from the string
            serialContent = serialContent.substring(index + 1);
        }

        return true;
    }
    return false;
}

// Feedback to pyhton after a move has been exectuted
void MoveDone()
{
    Serial.println(true);
}

void Homing()
{
    // Test vacuum
    digitalWrite(vacuum, true);
    delay(2000);
    digitalWrite(vacuum, false);
    delay(100);

    // Home Z
    while (!digitalRead(limitSwitchZ))
    {
        stepperZ.setSpeed(1000);
        stepperZ.runSpeed();
        stepperZ.setCurrentPosition(14000);
    }
    delay(20);
    // Move stepper Z to start postion
    stepperZ.moveTo(0);
    while (stepperZ.currentPosition() != 0)
    {
        stepperZ.run();
    }

    delay(100);

    // Home Arm
    while (!digitalRead(limitSwitchArm))
    {
        stepperArm.setSpeed(-800);
        stepperArm.runSpeed();
        stepperArm.setCurrentPosition(-1400);
    }
    delay(20);
    // Move stepper Arm to start postion
    stepperArm.moveTo(0);
    while (stepperArm.currentPosition() != 0)
    {
        stepperArm.run();
    }

    delay(100);

    // Home Base
    while (!digitalRead(limitSwitchBase))
    {
        stepperBase.setSpeed(-800);
        stepperBase.runSpeed();
        stepperBase.setCurrentPosition(-1200);
    }
    delay(20);
    // Move stepper Arm to start postion
    stepperBase.moveTo(0);
    while (stepperBase.currentPosition() != 0)
    {
        stepperBase.run();
    }

    delay(100);
}
