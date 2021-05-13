from App_Util import scan_serial_ports, beacon_collection
from GroundStationGUI import MainApp
import App_Parameters as app_params
import multiprocessing
import tkinter as tk
import threading
import os

# Testing flag
from Testing import IS_TESTING

# Start running GUI
if __name__ == "__main__":

    # To fix the multiple tkinter window spawning problem
    multiprocessing.freeze_support()

    # Check folder path to save CSV file
    if not os.path.exists(app_params.HOUSEKEEPING_DATA_FOLDER_FILEPATH):
        os.makedirs(app_params.HOUSEKEEPING_DATA_FOLDER_FILEPATH)

    # Scan for serial ports
    ports = scan_serial_ports()
    ports.insert(0, " ")

    # In testing, add dummy entries
    if IS_TESTING:
        ports.append("COM14")
        ports.append("COM15")

    # Create pipes for beacon
    pipe_beacon, pipe_gui = multiprocessing.Pipe(True)

    # Initialize Tk GUI in main thread
    root = tk.Tk()
    MainApp(root, ports, pipe_gui)

    # Thread to read data
    beacon_thread = threading.Thread(
        target=beacon_collection, daemon=True, args=(pipe_beacon,))
    beacon_thread.start()

    # Start Tk GUI in main thread
    root.mainloop()
