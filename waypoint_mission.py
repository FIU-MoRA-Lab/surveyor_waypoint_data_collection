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

def allocate_data_df(boat):
    """
    Allocate a DataFrame to store the boat's data.

    Args:
        boat (Surveyor): The Surveyor object representing the boat.

    Returns:
        pd.DataFrame: A DataFrame containing the boat's initial data.
    """
    return pd.DataFrame([boat.get_data()])

def start_mission(boat, count = 5):
    """
    Start the mission by waiting for the operator to switch to waypoint mode.

    Args:
        boat (Surveyor): The Surveyor object representing the boat.
    """
    print('Ready to start the mission! Switch manually to waypoint mode')
    # boat.set_standby_mode()

    while boat.get_control_mode() != "Waypoint":
        pass

    countdown(count, "Starting mission in", "Change the operator to secondary mode!")
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

def load_and_send_waypoint(boat, waypoint, erp, throttle, tolerance_meters = 2.0):
    """
    Load the next waypoint and send it to the boat.

    Args:
        boat (Surveyor): The Surveyor object representing the boat.
        waypoint (tuple): The waypoint coordinates to be sent.
        erp (list): A list of ERP coordinates.
        throttle (int): The desired throttle value for the boat.
        tolerance_meters (float): The tolerance distance for the waypoint in meters. If the waypoint is within the margin, it will be loaded only once.
    """
    boat.send_waypoints([waypoint], erp, throttle)
    dist = tolerance_meters + 1

    while boat.get_control_mode() != 'Waypoint' and dist > tolerance_meters:
        print(f'Distance to next waypoint {dist := geodesic(waypoint, boat.get_gps_coordinates()).meters}')
        boat.set_waypoint_mode()

def has_detected_anomaly(coordinates):
    """
    Check if an anomaly has been detected at the given coordinates.

    Args:
        coordinates (tuple): A tuple containing the latitude and longitude.

    Returns:
        bool: True if an anomaly has been detected, False otherwise.
    """
    ANOMALY_LAT = 25.9096626
    ANOMALY_LON = -80.1370655
    ANOMALY_COORDINATES = (ANOMALY_LAT, ANOMALY_LON)
    TOLERANCE = 3  # meters

    return hlp.are_coordinates_close(coordinates, ANOMALY_COORDINATES, TOLERANCE)

def patrol_square_area(boat, current_coordinates, desired_coordinates, erp):
    """
    Patrol a 5-meter square area around the current position and continue to the desired waypoint.

    Args:
        boat (Surveyor): The Surveyor object representing the boat.
        current_coordinates (tuple): The current latitude and longitude coordinates.
        desired_coordinates (tuple): The desired waypoint coordinates.
        erp (list): A list of ERP coordinates.
    """
    # Create a 5-meter side square around the current position
    square_coordinates = hlp.create_square_coordinates(current_coordinates, 5)

    # Create a waypoint message DataFrame for the square and the desired waypoint
    square_df = hlp.create_way_point_messages_df_from_list(square_coordinates + [desired_coordinates], erp)
    erp_nmea_message = square_df.iloc[0]['nmea_message']
    
    # Send waypoints for the square
    boat.set_station_keep_mode()
    boat.send_waypoints(square_df[1:], erp_nmea_message, 20)
    while boat.get_control_mode() != 'Waypoint':
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
        print(f'{message} {i}. {additional_message}', end="\r")
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
    # print(waypoints, erp)
    
    THROTTLE = 30  # Default throttle value
    index = 0 # Initialization variables
    ONLY_AT_WAYPOINT = True # Set it to true if you want a separate data csv file collected ONLY at the waypoints

    boat = surveyor.Surveyor()
    with boat:
        start_mission(boat)
        data_df = allocate_data_df(boat)
        current_coordinates = tuple(data_df[['Latitude'], ['Longitude']].iloc[-1])

        while index < len(waypoints):
            patrolling = False
            print(f'Loading waypoint #{index + 1}', end="\r")
            desired_coordinates = waypoints[index]
            boat.go_to_waypoint(desired_coordinates, erp, THROTTLE)

            while (control_mode := boat.get_control_mode()) != "Station Keep":

                if control_mode == "Go To ERP":
                    print("Going to ERP, aborting mission")
                    sys.exit(1)
                elif control_mode != 'Waypoint':
                    print(f"{control_mode} mode")
                    continue

                print(f"Navigating to waypoint #{index + 1}", end="\r")

                if not is_clear(boat):
                    avoid_obstacle(boat)

                if has_detected_anomaly(current_coordinates) and not patrolling:
                    print("Investigating anomaly")
                    patrolling = True
                    patrol_square_area(boat, current_coordinates, desired_coordinates, erp)

                data = hlp.process_gga_and_save_data(boat, post_fix = mission_postfix)
                data_df = pd.concat([data_df, pd.DataFrame([data])], ignore_index=True)
                current_coordinates = tuple(data[['Latitude'], ['Longitude']])
                print(f'Meters to next waypoint {geodesic(current_coordinates,desired_coordinates ).meters }', end = "\r")

            if hlp.are_coordinates_close(boat.get_gps_coordinates(), desired_coordinates, tolerance_meters = 4.0):
                print('Successful waypoint')
                if ONLY_AT_WAYPOINT:
                    hlp.process_gga_and_save_data(boat, post_fix = mission_postfix + 'only_waypoints')
                index += 1
            else:
                print('Failed waypoint')
                # TODO: Implement maximum number of retries.

    print("Mission completed.")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) not in [3, 4]:
        print("Usage: python converter.py <filename> <erp_filename> <mission_postfix>")
        sys.exit(1)

    main(*sys.argv[1:])

