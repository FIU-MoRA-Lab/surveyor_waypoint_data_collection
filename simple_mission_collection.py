import argparse
import logging

import surveyor_library.helpers as hlp
import surveyor_library.surveyor as surveyor

if __name__ == "__main__":
    mission_description = (
        "Simple data collection mission, intended for data collection while controling the boat"
        "manually. Data is saved as a .csv file at out/<todays date><mission_postfix>.csv"
    )
    print(mission_description)
    parser = argparse.ArgumentParser(description=mission_description)

    # Add required positional arguments
    parser.add_argument(
        "mission_postfix",
        type=str,
        nargs="?",
        default="",
        help="Optional mission postfix.",
    )

    # Parse the command line arguments
    args = parser.parse_args()
    boat = surveyor.Surveyor(
        sensors_to_use=["exo2", "camera"], logger_level=logging.INFO
    )
    data_to_be_collected = ["state", "exo2"]

    with boat:
        while True:
            print(
                hlp.process_gga_and_save_data(
                    boat,
                    data_keys=data_to_be_collected,
                    post_fix=args.mission_postfix,
                    delay=1.0,
                )
            )
