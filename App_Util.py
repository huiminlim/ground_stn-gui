import os
import random
import sys
import time

import serial

import CCSDS_Parameters as ccsds_params
from CCSDS_Decoder import CCSDS_Decoder
from CCSDS_Encoder import CCSDS_Encoder
from CCSDS_HK_Util import CCSDS_HK_Util
from Testing import IS_TESTING


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # pylint: disable=no-member
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def beacon_collection(pipe_beacon):
    """
    Collects beacons inputs from serial ports and sends out via pipes to GUI.

    Args:
        pipe_beacon (Connection): Pipe to send out beacon inputs collected.
    """

    def setup_serial(port):
        ttnc_ser = serial.Serial(port)
        ttnc_ser.baudrate = 9600
        ttnc_ser.timeout = 0.8
        return ttnc_ser

    # Setup CCSDS Decoder
    Decoder = CCSDS_Decoder(isBeacon=True, isHK=False)

    while pipe_beacon.poll() == b"":
        pass

    # Obtain ttnc serial port object
    ttnc_serial_port = pipe_beacon.recv()

    # Setup ttnc port serial object
    if not IS_TESTING:
        ttnc_ser = setup_serial(ttnc_serial_port)
        # print("first setup serial done")

    # Setup ttnc serial port
    temp = 0
    gx = 0
    gy = 0
    gz = 0
    adc = 0
    ax = 0
    ay = 0
    az = 0
    ts_date = 0
    ts_time = 0
    pipe_beacon.send([temp, gx, gy, gz, adc, ax, ay, az, ts_date, ts_time])

    isStopBeacon = False
    while True:

        if IS_TESTING:
            temp = f"{random.randrange(20, 40)}"
            gx = f"{random.randint(-50, 50)}"
            gy = f"{random.randint(-50, 50)}"
            gz = f"{random.randint(-50, 50)}"
            ax = f"{random.randint(-50, 50)}"
            ay = f"{random.randint(-50, 50)}"
            az = f"{random.randint(-50, 50)}"
            adc = f"{random.randrange(2, 8)}"
            ts_date = "00/00/00"
            ts_time = "00:00:00"
            # print("beacon", temp, gx, gy, gz, adc, ax, ay, az)
            time.sleep(10)
            pipe_beacon.send([temp, gx, gy, gz, adc, ax, ay, az, ts_date, ts_time])
            continue

        # If receive signal to close serial port
        if pipe_beacon.poll() == True:
            recv = pipe_beacon.recv()
            # print(f"beacon process {recv}")

            if recv == "close_serial":
                ttnc_ser.close()
                pipe_beacon.send("done")
                isStopBeacon = True
                # print("close serial")

            if recv == "open_serial":
                ttnc_ser = setup_serial(ttnc_serial_port)
                isStopBeacon = False

        if not isStopBeacon:
            # Read beacon packets
            # print("reading beaconds")
            ccsds_beacon_bytes = ttnc_ser.read(
                ccsds_params.CCSDS_BEACON_LEN_BYTES)
            # print(ccsds_beacon_bytes)
            # lock.release()

            if ccsds_beacon_bytes:
                try:
                    decoded_ccsds_beacon = Decoder.parse_beacon(
                        ccsds_beacon_bytes)
                except IndexError:
                    continue

                temp = f"{decoded_ccsds_beacon.get_temp():.2f}"
                adcs = decoded_ccsds_beacon.get_adcs_data()
                gx = f"{adcs['gx']:.3f}"
                gy = f"{adcs['gy']:.3f}"
                gz = f"{adcs['gz']:.3f}"
                ax = f"{adcs['ax']:.3f}"
                ay = f"{adcs['ay']:.3f}"
                az = f"{adcs['az']:.3f}"
                ts_date = decoded_ccsds_beacon.get_timestamp_date()
                ts_time = decoded_ccsds_beacon.get_timestamp_time()
                adc = f"{decoded_ccsds_beacon.get_vbatt():.2f}"

                # print("beacon", temp, gx, gy, gz, ax, ay, az)
                pipe_beacon.send([temp, gx, gy, gz, adc, ax, ay, az, ts_date, ts_time])


# Process to get housekeeping logs
def process_get_HK_logs(pipe, ttnc_serial_port):

    def setup_serial(port):
        ttnc_ser = serial.Serial(port)
        ttnc_ser.baudrate = 9600
        ttnc_ser.timeout = 10
        return ttnc_ser

    Encoder = CCSDS_Encoder()
    HK_Util = CCSDS_HK_Util()

    # Default for command
    timestamp_query_start = '0-0-0-0-0-0'
    timestamp_query_end = '0-0-0-0-0-0'

    telecommand = Encoder.generate_HK_telecommand(
        ccsds_params.TELECOMMAND_TYPE_OBC_HK_REQUEST, timestamp_query_start, timestamp_query_end)

    pipe.send("close_serial")
    while pipe.poll() == "":
        pass
    print(f"process receive {pipe.recv()}")

    ttnc_serial = setup_serial(ttnc_serial_port)

    print(f"telecommand is {telecommand}")
    print(f"telecommand len is {len(telecommand)}")
    ttnc_serial.write(telecommand)
    hk_bytes = ttnc_serial.read(
        ccsds_params.CCSDS_OBC_TELEMETRY_LEN_BYTES)
    # print(f"hk bytes {hk_bytes}")
    # print(f"len hk bytes {len(hk_bytes)}")

    print("done sending command")
    ttnc_serial.close()
    pipe.send("open_serial")

    if hk_bytes:
        list_hk_obj = HK_Util.parse(hk_bytes)
        HK_Util.log(list_hk_obj)
        print("done do logs")
    else:
        print("hk logs failed")


# Sample process to run in place of HK telecommand in testing mode
def sample_hk_command_process():
    i = 0
    max_val = 50000

    while i < max_val:
        print(i)
        i += 1
