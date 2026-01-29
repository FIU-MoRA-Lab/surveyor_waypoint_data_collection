#!/usr/bin/env python3
"""
GPS Coordinate Plotter with Satellite Imagery

This standalone utility plots GPS coordinates from CSV files on satellite imagery
using Cartopy and Google Satellite tiles. Useful for visualizing waypoint missions,
recorded trajectories, or any GPS data on real-world satellite maps.
"""

import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_points_with_satellite(csv_file, zoom=18):
    """
    Plot GPS coordinates from a CSV file on satellite imagery.
    Differentiates start/goal and shows path direction with arrows.
    """
    # Read CSV
    df = pd.read_csv(csv_file)
    lats = df["Latitude"].values
    lons = df["Longitude"].values

    if len(lats) < 2:
        print("Not enough points to plot a path.")
        return

    # Compute bounds with buffer
    mean_lat = np.mean(lats)
    delta_lat = 20 / 111000.0
    delta_lon = 20 / (111320.0 * np.cos(np.radians(mean_lat)))

    min_lat, max_lat = lats.min() - delta_lat, lats.max() + delta_lat
    min_lon, max_lon = lons.min() - delta_lon, lons.max() + delta_lon

    # Set up Google satellite tiles
    tiler = cimgt.GoogleTiles(style="satellite")
    img_crs = tiler.crs

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(1, 1, 1, projection=img_crs)
    ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=ccrs.PlateCarree())
    ax.add_image(tiler, zoom)

    # Plot the full trajectory line
    ax.plot(
        lons,
        lats,
        color="cyan",
        linewidth=2,
        transform=ccrs.PlateCarree(),
        zorder=9,
        alpha=0.7,
    )

    # Add direction arrows (every few points to avoid clutter)
    step = max(1, len(lons) // 10)
    for i in range(0, len(lons) - 1, step):
        x1, y1 = lons[i], lats[i]
        x2, y2 = lons[i + 1], lats[i + 1]
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", color="yellow", lw=1.5),
            transform=ccrs.PlateCarree(),
        )

    # Differentiate Start and Goal
    # Start point (Green)
    ax.scatter(
        lons[0],
        lats[0],
        color="lime",
        s=100,
        edgecolors="black",
        label="Start",
        transform=ccrs.PlateCarree(),
        zorder=11,
    )

    # Goal point (Red/X)
    ax.scatter(
        lons[-1],
        lats[-1],
        color="red",
        s=100,
        edgecolors="white",
        marker="X",
        label="Goal",
        transform=ccrs.PlateCarree(),
        zorder=11,
    )

    # Plot intermediate points
    ax.scatter(
        lons[1:-1],
        lats[1:-1],
        color="white",
        s=10,
        transform=ccrs.PlateCarree(),
        zorder=10,
    )

    ax.coastlines(resolution="10m", color="white", linewidth=1)
    plt.title(f"Mission Path: {csv_file}")
    plt.legend(loc="upper right")
    plt.show()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python plot_coordinates.py <csv_file> [zoom_level]")
        sys.exit(1)

    zoom_level = int(sys.argv[2]) if len(sys.argv) > 2 else 19
    plot_points_with_satellite(sys.argv[1], zoom=zoom_level)
