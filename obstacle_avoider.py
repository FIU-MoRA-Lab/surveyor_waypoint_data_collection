import numpy as np


class obstacleAvoiderController:
    def __init__(
        self,
        care_fov=np.pi / 2,
        safe_dist=2.0,
        T_default=20.0,
        k_theta=1.0,
        adaptive_fov=False,
        ignore_dist=0.25,
        deg2rad=False,
    ):
        """
        Initialize the obstacle avoider controller.

        Parameters:
        - care_fov: Field of view (FOV) for obstacle avoidance (default: π/2).
        - safe_dist: Safe distance threshold for obstacles (default: 2.0 meters).
        - T_default: Default thrust value (default: 20.0).
        - k_theta: Angular correction gain (default: 1.0).
        - adaptive_fov: Flag for enabling adaptive FOV based on distance (default: False).
        """
        self.care_fov = care_fov / 2  # Consider only half for symmetric FOV
        self.safe_dist = safe_dist
        self.T_default = T_default
        self.k_theta = k_theta
        self.adaptive_fov = adaptive_fov
        self.ignore_dist = ignore_dist  # Ignore distances below this threshold
        self.deg2rad = deg2rad  # Flag for angle conversion

        # Internal state
        self._upd_care_fov = self.care_fov
        self._min_distance = self.safe_dist

    def _adaptive_angle(self, min_distance):
        """
        Compute an adaptive field of view based on the closest obstacle distance.

        Parameters:
        - min_distance: Distance to the nearest obstacle.

        Returns:
        - Adjusted FOV.
        """
        diff = np.sign(min_distance - self.safe_dist) * abs(
            min_distance - self.safe_dist
        )
        return (
            (np.pi / 2 - self.care_fov) / (0.5 - self.safe_dist)
        ) * diff + self.care_fov

    def compute_control(self, lidar_measurements):
        """
        Compute control action based on lidar measurements.

        Parameters:
        - lidar_measurements: Tuple (distances, angles) from the lidar sensor.

        Returns:
        - control: Numpy array [thrust, thrust_diff] or None if no avoidance is needed.
        """
        distances, angles = lidar_measurements
        distances, angles = np.asarray(distances), np.asarray(angles)
        # print(distances.shape, angles.shape)
        # Convert angles to radians if necessary
        if self.deg2rad:
            angles = (np.deg2rad(angles) + np.pi) % (2 * np.pi) - np.pi

        # Find minimum distance in the standard FOV (-π/2 to π/2)
        min_distance = np.min(
            distances[
                (-np.pi / 2 <= angles)
                & (angles <= np.pi / 2)
                & (distances > self.ignore_dist)
            ],
            initial=self.safe_dist,
        )
        self._min_distance = min_distance

        # Update FOV if adaptive mode is enabled
        self._upd_care_fov = (
            self._adaptive_angle(min_distance) if self.adaptive_fov else self.care_fov
        )

        # Filter lidar data within the updated FOV
        fov_mask = (-self._upd_care_fov <= angles) & (angles <= self._upd_care_fov)
        valid_mask = fov_mask & (distances > self.ignore_dist)
        filtered_distances = distances[valid_mask]
        filtered_angles = angles[valid_mask]
        print(self._upd_care_fov)

        nearest_dist = np.min(filtered_distances, initial=self.safe_dist)
        print(f"Nearest obstacle distance: {nearest_dist:.2f} meters")
        if nearest_dist >= self.safe_dist:
            print("Obs not in upd fov")
            return None

        # Compute mean angle of obstacles closer than safe threshold
        # print((filtered_distances <= self.safe_dist).shape)
        mean_angle = np.mean(filtered_angles[filtered_distances <= self.safe_dist])

        # Compute thrust differential for avoidance maneuver
        factor = 1 - abs(mean_angle / np.pi)
        thrust_diff = (
            -np.sign(mean_angle)
            * self.k_theta
            * factor
            * (self.safe_dist / nearest_dist) ** 0.5
        )
        # Apply thresholds to the thrust differential
        if abs(thrust_diff) < 5:
            thrust_diff = 0
        elif 5 < abs(thrust_diff) < 10:
            thrust_diff = 10 * np.sign(thrust_diff)

        # Compute thrust, ensuring a minimum motion threshold
        thrust = self.T_default * min(nearest_dist / self.safe_dist, 0.5)

        return np.array([thrust, thrust_diff])
