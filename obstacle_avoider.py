import numpy as np
import logging

class ObstacleAvoiderController:
    def __init__(
        self,
        care_fov=np.pi / 2,
        safe_dist=2.0,
        T_default=20.0,
        k_theta=1.0,
        adaptive_fov=False,
        ignore_dist=0.25,
        deg2rad=False,
        logging_level=logging.INFO
    ):
        """
        Initialize the obstacle avoider controller.

        Parameters:
        - care_fov (float): Field of view (FOV) for obstacle avoidance in radians (default: π/2).
        - safe_dist (float): Safe distance threshold for obstacles in meters (default: 2.0).
        - T_default (float): Default thrust value (default: 20.0).
        - k_theta (float): Angular correction gain (default: 1.0).
        - adaptive_fov (bool): Flag for enabling adaptive FOV based on distance (default: False).
        - ignore_dist (float): Minimum distance to ignore obstacles (default: 0.25 meters).
        - deg2rad (bool): Flag for angle conversion from degrees to radians (default: False).
        """
        if care_fov <= 0 or safe_dist <= 0 or T_default <= 0 or ignore_dist < 0:
            raise ValueError("Invalid parameter values provided.")

        self.care_fov = care_fov / 2  # Consider only half for symmetric FOV
        self.safe_dist = safe_dist
        self.T_default = T_default
        self.k_theta = k_theta
        self.adaptive_fov = adaptive_fov
        self.ignore_dist = ignore_dist
        self.deg2rad = deg2rad

        # Internal state
        self._upd_care_fov = self.care_fov
        self._min_distance = self.safe_dist

        # Precompute constants
        self.half_pi = np.pi / 2
        self.adaptive_fov_factor = (
            (self.half_pi - self.care_fov) / self.safe_dist
        )

        # Logging setup
        logging.basicConfig(level=logging_level)

    def _adaptive_angle(self, min_distance):
        """
        Compute an adaptive field of view based on the closest obstacle distance.

        Parameters:
        - min_distance: Distance to the nearest obstacle.

        Returns:
        - Adjusted FOV.
        """
        if min_distance >= self.safe_dist:
            return self.care_fov
        diff = (self.safe_dist - min_distance) ** .5
        return self.care_fov + diff * self.adaptive_fov_factor

    def is_clear(self, lidar_measurements):
        """
        Check if there are obstacles within the avoidance controller's field of view.

        Parameters:
        - obstacles: List of obstacles.

        Returns:
        - True if an obstacle is too close, False otherwise.
        """
        distances, angles = lidar_measurements
        # Filter lidar data within the relevant field of view
        # Precompute masks
        valid_distances_mask = (distances > self.ignore_dist) & (distances < self.safe_dist)
        fov_mask = (-self._upd_care_fov <= angles) & (angles <= self._upd_care_fov)
        combined_mask = valid_distances_mask & fov_mask

        if not np.any(combined_mask):
            logging.info("No obstacles detected in the lidar data.")
            return True, np.array([]), np.array([])
        else:
            logging.info("Obstacles detected in the lidar data.")
            filtered_distances = distances[combined_mask]
            filtered_angles = angles[combined_mask]
            return False, filtered_distances, filtered_angles

    def compute_control(self, lidar_measurements):
        """
        Compute control action based on lidar measurements.

        Parameters:
        - lidar_measurements (tuple): Tuple (distances, angles) from the lidar sensor.

        Returns:
        - control (numpy.ndarray): Array [thrust, thrust_diff] or None if no avoidance is needed.
        """
        distances, angles = lidar_measurements
        # Convert angles to radians if necessary
        if self.deg2rad:
            angles_in_radians = np.deg2rad(angles)
            angles = (angles_in_radians + np.pi) % (2 * np.pi) - np.pi

        if self.adaptive_fov:
            # Compute adaptive field of view based on the closest obstacle distance
            min_distance = np.min(
            distances[
                (-self.half_pi <= angles)
                & (angles <= self.half_pi)
                & (distances > self.ignore_dist)
            ],
            initial=self.safe_dist,
            )
            self._upd_care_fov = self._adaptive_angle(min_distance)
            logging.info(f"Adaptive FOV updated to: {np.rad2deg(self._upd_care_fov):.2f} degrees")

        is_clear, filtered_distances, filtered_angles = self.is_clear(lidar_measurements)
        if is_clear:
            return None
        # Obstacles detected, proceed with avoidance maneuver
        # Compute nearest distance
        nearest_dist = np.min(filtered_distances)
        # Compute mean angle of obstacles
        mean_angle = np.mean(filtered_angles)
        logging.info(f"Nearest obstacle: {nearest_dist:.2f} meters at angle {np.rad2deg(mean_angle):.2f} degrees")

        # Compute thrust differential for avoidance maneuver
        factor = 1 - abs(mean_angle / np.pi)
        thrust_diff = (
            -np.sign(mean_angle)
            * self.k_theta
            * factor
            * (self.safe_dist / nearest_dist)
        )
        # Compute thrust, ensuring a minimum motion threshold
        thrust = self.T_default * min(nearest_dist / self.safe_dist, 0.5)
        control = np.array([thrust, thrust_diff])
        logging.debug(f"Control computed: thrust={thrust:.2f}, thrust_diff={thrust_diff:.2f}")
        return control
