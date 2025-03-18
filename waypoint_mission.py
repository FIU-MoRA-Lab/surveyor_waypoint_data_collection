"""
This module runs a waypoint mission collecting water quality data from the Exo2 sensor.
Inputs:
    CSV file containing the waypoints to be visited.
    CSV file containing the Emergency Recovery Point (ERP).
    See the 'main' function for more details.
"""
import sys
import time
import pandas as pd
import surveyor_library.helpers as hlp
import surveyor_library.surveyor as surveyor
from geopy.distance import geodesic
import argparse
import logging


def start_mission(boat, count = 5):
    """
    Start the mission by waiting for the operator to switch to waypoint mode.

    Args:
        boat (Surveyor): The Surveyor object representing the boat.
    """
    boat.set_standby_mode()
    countdown(count, "Starting mission in", "!")
    print('Mission started!')

def is_clear(boat):
    """
    Check if the path is clear for the boat to navigate.

    Args:
        boat (Surveyor): The Surveyor object representing the boat.

    Returns:
        bool: True if the path is clear, False otherwise.
    """
    return True

def avoid_obstacle(boat):
    """
    Perform actions to avoid an obstacle in the boat's path.

    Args:
        boat (Surveyor): The Surveyor object representing the boat.
    """
    boat.set_standby_mode()
    print("Obstacle detected, waiting for 10 seconds to see if it moves.")
    time.sleep(10)
    if not is_clear(boat):
        boat.set_erp_mode()
        print("Obstacle not cleared, aborting mission.")
        sys.exit(1)
    print("Obstacle avoided, resuming navigation")
    boat.set_waypoint_mode()


def countdown(count, message, additional_message=""):
    """
    Print a countdown with the given message and optional additional message.

    Args:
        count (int): The number of seconds to count down.
        message (str): The message to display before the countdown.
        additional_message (str, optional): An additional message to display after the countdown.
    """
    for i in range(count, 0, -1):
        print(f'{message} {i} {additional_message}', end="\r")
        time.sleep(1)
    print()

def main(filename, erp_filename, mission_postfix= ""):
    """
    Main function to execute the surveyor boat mission.

    Args:
        filename (str): The path to the file containing waypoints.
        erp_filename (str): The path to the file containing ERP data.
        mission_postfix (str): The suffix to be appended to the name if the CSV file containing the data.
    """
    print(f'Reading waypoints from {filename} and ERP from {erp_filename}')
    waypoints = hlp.read_csv_into_tuples(filename)
    erp = hlp.read_csv_into_tuples(erp_filename)
    
    THROTTLE = 25  # Default throttle value
    index = 0 # Initialization variables
    ONLY_AT_WAYPOINT = False # Set it to true if you want a separate data csv file collected ONLY at the waypoints
    data_to_be_collected = ['state', 'exo2']

    boat = surveyor.Surveyor(sensors_to_use=['exo2', 'camera'],
                             sensors_config={'exo2': {'exo2_server_ip': '192.168.0.68'},
                                            'camera': {},
                                            'lidar': {}},
                             logger_level=logging.INFO
                            )
    with boat:
        start_mission(boat, 1)
        print(pd.DataFrame([boat.get_data(data_to_be_collected)])) #Show example of data being collected
        current_coordinates = boat.get_gps_coordinates()

        while index < len(waypoints):

            print(f'Loading waypoint #{index + 1}')
            desired_coordinates = waypoints[index]
            boat.go_to_waypoint(desired_coordinates, erp, THROTTLE)

            
            while (control_mode := boat.get_control_mode()) != "Station Keep":

                if control_mode == "Go To ERP":
                    print("Going to ERP, aborting mission")
                    sys.exit(1)
                elif control_mode != 'Waypoint':
                    print(f"{control_mode} mode")
                    continue

                print(f"Navigating to waypoint #{index + 1}")

                if not is_clear(boat):
                    avoid_obstacle(boat)

                data = hlp.process_gga_and_save_data(boat, data_keys = data_to_be_collected, post_fix = mission_postfix) # You may save and retreive data at the same time
                
                current_coordinates = boat.get_gps_coordinates()
                print(f'Meters to next waypoint {geodesic(current_coordinates,desired_coordinates ).meters:.2f}')

            if hlp.are_coordinates_close(boat.get_gps_coordinates(), desired_coordinates, tolerance_meters = 2.5):
                print('Successful waypoint')
                if ONLY_AT_WAYPOINT:
                    hlp.process_gga_and_save_data(boat, data_keys = data_to_be_collected, post_fix = mission_postfix + 'only_waypoints')
                index += 1
            else:
                print('Failed waypoint')
                # TODO: Implement maximum number of retries.

    print("Mission completed.")
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Waypoint mission script.')

    # Add required positional arguments
    parser.add_argument('filename', type=str, help='The filename for waypoints.')
    parser.add_argument('erp_filename', type=str, help='The filename for ERP.')
    
    # Add optional argument with a default value
    parser.add_argument('mission_postfix', type=str, nargs='?', default='', help='Optional mission postfix.')

    # Parse the command line arguments
    args = parser.parse_args()

    # Call the main function with parsed arguments
    main(args.filename, args.erp_filename, args.mission_postfix)

