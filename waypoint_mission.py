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
import surveyor_library.surveyor_helper as hlp
import surveyor_library.surveyor as surveyor
from geopy.distance import geodesic

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
    
    THROTTLE = 15  # Default throttle value
    index = 0 # Initialization variables
    ONLY_AT_WAYPOINT = True # Set it to true if you want a separate data csv file collected ONLY at the waypoints
    data_to_be_collected = ['coordinates', 'heading']

    boat = surveyor.Surveyor()
    with boat:
        start_mission(boat, 1)
        data_df = pd.DataFrame([boat.get_data(data_to_be_collected)]) #Allocating data
        print(data_df)
        current_coordinates = tuple(data_df[['Latitude', 'Longitude']].iloc[-1])

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

                data = hlp.process_gga_and_save_data(boat, data_keys = data_to_be_collected, post_fix = mission_postfix)
                data_df = pd.concat([data_df, pd.DataFrame([data])], ignore_index=True)
                current_coordinates = tuple(data_df[['Latitude', 'Longitude']].iloc[-1])
                print(f'Meters to next waypoint {geodesic(current_coordinates,desired_coordinates ).meters:.2f}')

            if hlp.are_coordinates_close(boat.get_gps_coordinates(), desired_coordinates, tolerance_meters = 2.0):
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
    if len(sys.argv) not in [3, 4]:
        print("Usage: python waypoint_mission.py <filename> <erp_filename> <mission_postfix>")
        sys.exit(1)

    main(*sys.argv[1:])

