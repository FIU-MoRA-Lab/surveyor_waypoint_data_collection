#!/usr/bin/env python3
"""
Trajectory Subsampling Utility

Usage:
    python subsample.py <trajectory_file.csv> <n_points> [--save]

Example:
    python subsample.py ../out/recorded_mission.csv 50 --save
"""

import argparse
import os

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cartopy.io.img_tiles import GoogleTiles


def subsample_trajectory(file_path, n_points, output_path=None):
    """
    Subsample a trajectory to a specified number of representative points.
    """
    # Read input file
    trajectory = pd.read_csv(file_path)

    # Use first two columns as coordinates (Assuming [Lon, Lat])
    cols = trajectory.columns[:2]
    points = trajectory[cols].values

    # Uniformly sample n_points
    indices = np.linspace(0, len(points) - 1, n_points, dtype=int)
    sampled_points = points[indices]

    # Create DataFrame for sampled points
    sampled_points_df = pd.DataFrame(sampled_points, columns=cols)

    # Save output file only if output_path is provided
    if output_path:
        sampled_points_df.to_csv(output_path, index=False)
        print(f"Saved {n_points} representative points to {output_path}")

    return points, sampled_points


def plot_trajectory_comparison(original_points, sampled_points, column_names):
    """
    Plot original trajectory alongside sampled representative points on a satellite map.
    """
    # Initialize satellite imagery tile source
    tiler = GoogleTiles(style="satellite")

    plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=tiler.crs)

    # Set extent around the data (lon_min, lon_max, lat_min, lat_max)
    lats = original_points[:, 0]
    lons = original_points[:, 1]
    margin = 20 / 111000.0  # Small margin for visibility
    ax.set_extent(
        [
            lons.min() - margin,
            lons.max() + margin,
            lats.min() - margin,
            lats.max() + margin,
        ],
        crs=ccrs.PlateCarree(),
    )

    # Add imagery with zoom level (18 is usually good for waypoint inspection)
    ax.add_image(tiler, 18)

    # Plot original path
    ax.plot(
        lons,
        lats,
        label="Original trajectory",
        color="cyan",
        alpha=0.8,
        transform=ccrs.PlateCarree(),
    )

    # Plot sampled points
    ax.scatter(
        sampled_points[:, 1],
        sampled_points[:, 0],
        color="red",
        s=30,
        # zorder=5,
        label=f"{len(sampled_points)} sampled points",
        transform=ccrs.PlateCarree(),
    )

    plt.legend()
    plt.title("Trajectory and Representative Points (Satellite View)")
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Subsample trajectory data.")
    parser.add_argument("input_file", help="Path to the input CSV file")
    parser.add_argument("n_points", type=int, help="Number of points to sample")
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the result with '_subsampled.csv' suffix",
    )

    args = parser.parse_args()

    # Determine output path if save flag is set
    output_path = None
    if args.save:
        input_dir = os.path.dirname(args.input_file)
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        output_filename = f"{base_name}_subsampled.csv"
        output_path = os.path.join(input_dir, output_filename)

    # Subsample trajectory
    original_points, sampled_points = subsample_trajectory(
        args.input_file, args.n_points, output_path
    )

    # Get column names for labeling
    trajectory = pd.read_csv(args.input_file)
    column_names = trajectory.columns[:2].tolist()

    # Plot comparison with Satellite Map
    plot_trajectory_comparison(original_points, sampled_points, column_names)


if __name__ == "__main__":
    main()
