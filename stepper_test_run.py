import serial
import time

ser = serial.Serial("COM3", 115200, timeout=None)
time.sleep(2)

for i in range(1, 950):
    speed = 1000 - i

    x_delay = speed * 2
    y_delay = speed

    command = "X " + str(x_delay) + " Y " + str(y_delay) + "      \n"
    ser.write(command.encode(encoding='UTF-8'))

    time.sleep(0.001)

    line = ser.readline()
    if line:
        string = line.decode()
        print(string[:-2])

for i in range(950, 1, -1):
    speed = 1000 - i

    x_delay = speed * 2
    y_delay = speed

    command = "X " + str(x_delay) + " Y " + str(y_delay) + "      \n"
    ser.write(command.encode(encoding='UTF-8'))

    time.sleep(0.001)

    line = ser.readline()
    if line:
        string = line.decode()
        print(string[:-2])
