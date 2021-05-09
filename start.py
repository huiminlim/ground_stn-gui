from multiprocessing import Pipe, Process
from GroundStationGUI import MainApp
import App_Parameters as app_params
import tkinter as tk
import threading

# Serial port scan
import serial
import glob
import sys

# CCSDS
from CCSDS_Parameters import CCSDS_BEACON_LEN_BYTES
from CCSDS_Decoder import CCSDS_Decoder

# Testing flag
from Testing import IS_TESTING
import random
import time


def scan_serial_ports():
    ports = []
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    # else:
    #     raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def beacon_collection(pipe_beacon):
    # Setup CCSDS Decoder
    Decoder = CCSDS_Decoder()

    # Collect com port
    while pipe_beacon.poll() == b"":
        pass

    # Obtain ttnc serial port object
    ttnc_ser = pipe_beacon.recv()

    # Setup ttnc serial port
    temp = 0
    gx = 0
    gy = 0
    gz = 0

    while True:

        if IS_TESTING:
            temp = f"{random.randrange(20, 40)}"
            gx = f"{random.randint(-50, 50)}"
            gy = f"{random.randint(-50, 50)}"
            gz = f"{random.randint(-50, 50)}"
            print("beacon", temp, gx, gy, gz)
            time.sleep(10)
            pipe_beacon.send([temp, gx, gy, gz])
            continue

        # Read beacon packets
        ccsds_beacon_bytes = ttnc_ser.read(CCSDS_BEACON_LEN_BYTES)
        # print(ccsds_beacon_bytes)

        if ccsds_beacon_bytes:

            try:
                decoded_ccsds_beacon = Decoder.parse_beacon(ccsds_beacon_bytes)
            except IndexError:
                continue

            temp = f"{decoded_ccsds_beacon.get_temp():.2f}"
            gyro = decoded_ccsds_beacon.get_gyro()
            gx = f"{gyro['gx']}"
            gy = f"{gyro['gy']}"
            gz = f"{gyro['gz']}"

            # print("beacon", temp, gx, gy, gz)
            pipe_beacon.send([temp, gx, gy, gz])


# Start running GUI
if __name__ == "__main__":

    # Scan for serial ports
    ports = scan_serial_ports()
    ports.insert(0, " ")

    # In testing, add dummy entries
    if IS_TESTING:
        ports.append("COM14")
        ports.append("COM15")

    # Create pipe for between Tk GUI and data thread
    pipe_gui, pipe_beacon = Pipe()

    # Initialize Tk GUI in main thread
    root = tk.Tk()
    MainApp(root, pipe_gui, ports)

    # Thread to read data
    data_thread = threading.Thread(
        group=None, target=beacon_collection, args=(pipe_beacon, ))
    data_thread.setDaemon(True)
    data_thread.start()

    # Start Tk GUI in main thread
    root.mainloop()