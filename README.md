# Surveyor Waypoint Data Collection

A comprehensive system for autonomous waypoint-based missions using the Surveyor robotic platform. This project enables data collection through GPS waypoint navigation with synchronized camera, LiDAR, and telemetry recording.

## Overview

This repository provides mission control scripts and utilities for:
- Autonomous waypoint navigation missions
- Real-time sensor data collection (camera, LiDAR, GPS)
- Obstacle avoidance during autonomous navigation
- Data logging in HDF5 format with synchronized multi-modal data
- Post-mission data analysis and visualization

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Mission Scripts](#mission-scripts)
- [Utilities](#utilities)
- [Data Output](#data-output)
- [Surveyor Library](#surveyor-library)
- [Requirements](#requirements)

## Installation

### Clone the Repository

```bash
git clone --recurse-submodules https://github.com/yourusername/surveyor_waypoint_data_collection.git
cd surveyor_waypoint_data_collection
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Update Submodule

To pull the latest changes from the surveyor_library submodule:

```bash
git submodule update --remote surveyor_library
git add surveyor_library
git commit -m "Update surveyor_library submodule"
```

## Quick Start

### 1. Prepare Waypoint Mission

Create a waypoint file in `in/` directory. Example format (`in/square_mission.txt`):

```
25.7589, -80.3730
25.7590, -80.3730
25.7590, -80.3729
25.7589, -80.3729
```

### 2. Run Autonomous Waypoint Mission

```bash
python waypoint_mission.py
```

This script:
- Loads waypoints from `in/square_mission.txt`
- Navigates autonomously through each waypoint
- Saves trajectory to CSV format in `out/`

### 3. Collect Data with Manual Control

```bash
python simple_mission_collection.py
```

This script allows manual boat control while recording:
- Camera images
- LiDAR data
- GPS telemetry
- Saves data to HDF5 format in `out/records/`

### 4. Run Mission with Obstacle Avoidance

```bash
python waypoint_mission_with_OA.py
```

Adds real-time obstacle detection and avoidance during autonomous navigation.

## Mission Scripts

### `waypoint_mission.py`

Autonomous GPS waypoint navigation mission.

**Features:**
- Loads GPS waypoints from text file
- Sequential autonomous waypoint navigation
- CSV trajectory logging
- No sensor data recording (navigation only)

**Usage:**
```bash
python waypoint_mission.py
```

**Use case:** Test autonomous navigation paths, verify waypoint accuracy

### `simple_mission_collection.py`

Manual data collection with synchronized sensor recording.

**Features:**
- Manual boat control (drive the boat yourself)
- Synchronized multi-sensor data recording (HDF5)
- Records camera images, LiDAR scans, and GPS telemetry
- Real-time data logging

**Usage:**
```bash
python simple_mission_collection.py
```

**Use case:** Collect training data, survey areas, record sensor data while manually navigating

### `waypoint_mission_with_OA.py`

Advanced autonomous mission with obstacle avoidance capabilities.

**Features:**
- Autonomous waypoint navigation
- LiDAR-based obstacle detection
- Dynamic path adjustment
- Real-time collision avoidance
- Full data collection

**Usage:**
```bash
python waypoint_mission_with_OA.py
```

**Use case:** Autonomous missions in environments with obstacles

### `obstacle_avoider.py`

Standalone obstacle avoidance behavior module.

**Features:**
- Configurable detection zones
- Reactive obstacle avoidance
- Can be imported into other scripts

## Utilities

The `utils/` folder contains standalone tools for data processing and visualization:

### `dataset_preview.py`

Visualize HDF5 datasets with synchronized playback of camera, LiDAR, and GPS data.

```bash
python utils/dataset_preview.py out/records/mission_data.h5
```

**Features:**
- Real-time visualization of recorded missions
- Three-panel display: camera image, LiDAR polar plot, GPS trajectory
- Frame-by-frame telemetry output

**Suggested alternative names:** `visualize_hdf5_dataset.py`, `hdf5_dataset_viewer.py`

### `plot_coordinates.py`

Plot GPS coordinates on satellite imagery.

```bash
python utils/plot_coordinates.py out/square_mission.csv [zoom_level]
```

**Features:**
- Google Satellite tile overlay
- Automatic map bounds with 20m buffer
- Adjustable zoom levels (default: 19)
- Red markers for waypoints

**Suggested alternative names:** `plot_gps_on_satellite.py`, `visualize_coordinates.py`

### `subsample.py`

Reduce dense trajectory data to representative waypoints.

```bash
python utils/subsample.py out/recorded_trajectory.csv
```

**Features:**
- Uniform sampling (default: 25 points)
- Preserves trajectory shape
- Visualization of original vs. sampled path
- Output: `robot_3_path.csv`

**Suggested alternative names:** `subsample_trajectory.py`, `trajectory_simplifier.py`

### Data Conversion Utilities

- **`apm_to_csv_converter.py`**: Convert APM log files to CSV format
- **`degree_to_minutes_converter.py`**: Convert GPS coordinates between formats

### HDF5 Data Reader

Located in `out/records/hdf5_reader.py`:

```bash
# Print all records
python out/records/hdf5_reader.py mission_data.h5 --print-all

# View summary statistics
python out/records/hdf5_reader.py mission_data.h5 --summary

# Export to CSV
python out/records/hdf5_reader.py mission_data.h5 --csv output.csv

# Plot time series
python out/records/hdf5_reader.py mission_data.h5 --plot plot.png
```

## Data Output

### Directory Structure

```
out/
├── records/              # HDF5 sensor data recordings
│   ├── mission_YYYYMMDD_HHMMSS.h5
│   └── hdf5_reader.py   # Reader utility
└── *.csv                 # Trajectory and waypoint files
```

### HDF5 Data Format

Each HDF5 file contains structured arrays with synchronized data:

**Fields:**
- `Image`: Camera frames (BGR format)
- `Angles`: LiDAR scan angles (degrees)
- `Distances`: LiDAR distance measurements (meters)
- `Latitude`: GPS latitude (decimal degrees)
- `Longitude`: GPS longitude (decimal degrees)
- `Heading`: Robot heading (degrees)
- `Speed`: Ground speed (m/s)
- `Timestamp`: Unix timestamp

### CSV Output Files

- Mission trajectories with GPS coordinates
- Latitude/Longitude columns
- Compatible with plotting utilities

## Surveyor Library

This project uses the [surveyor_library](surveyor_library/) as a Git submodule, which provides:

- **Core Surveyor API**: High-level robot control interface
- **Client modules**: Camera, LiDAR, GPS/IMU clients
- **Server modules**: Sensor data servers for Raspberry Pi
- **Helper utilities**: HDF5 logging, waypoint management, message protocols
- **Documentation**: See `surveyor_library/surveyor_lib/docs/`

The library is maintained as a separate repository and can be used independently in other projects.

### Submodule Management

```bash
# Update to latest version
git submodule update --remote surveyor_library

# Pull changes manually
cd surveyor_library
git pull origin main
cd ..
```

For detailed documentation on the surveyor_library API, see the submodule's README and docs folder.

## Requirements

### Python Packages

```
numpy
pandas
matplotlib
opencv-python (cv2)
h5py
cartopy  # For satellite imagery plotting
```

Install all dependencies:

```bash
pip install -r requirements.txt
```

### Hardware Requirements

- Surveyor robot platform with:
  - GPS/IMU (Exo2 system)
  - Camera
  - LiDAR sensor
  - Raspberry Pi or compatible controller

### Network Requirements

- Robot control interface (typically WiFi or Ethernet)
- Internet connection for satellite imagery (plot_coordinates.py)

## Project Structure

```
surveyor_waypoint_data_collection/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
│
├── Mission Scripts/
│   ├── simple_mission_collection.py   # Basic waypoint mission with data collection
│   ├── waypoint_mission.py            # Core waypoint navigation
│   ├── waypoint_mission_with_OA.py    # Mission with obstacle avoidance
│   └── obstacle_avoider.py            # Obstacle avoidance module
│
├── in/                                # Input waypoint files
│   └── square_mission.txt             # Example mission
│
├── out/                               # Output data
│   ├── records/                       # HDF5 sensor recordings
│   │   └── hdf5_reader.py            # Data reader utility
│   └── *.csv                          # Trajectory files
│
├── utils/                             # Standalone utilities
│   ├── dataset_preview.py             # Visualize HDF5 datasets
│   ├── plot_coordinates.py            # GPS on satellite imagery
│   ├── subsample.py                   # Trajectory subsampling
│   ├── apm_to_csv_converter.py       # APM log converter
│   └── degree_to_minutes_converter.py # GPS format converter
│
└── surveyor_library/                  # Git submodule (robot control library)
    ├── surveyor_lib/
    │   ├── surveyor.py                # Main Surveyor API
    │   ├── clients/                   # Sensor clients
    │   ├── helpers/                   # Logging and utilities
    │   └── servers/                   # Sensor servers (Pi)
    └── docs/                          # Library documentation
```

## Contributing

When contributing to this project:

1. Keep surveyor_library submodule updates separate
2. Document new mission scripts in this README
3. Add standalone utilities to the `utils/` folder with proper documentation
4. Follow Python docstring conventions for all functions

## License

[Your License Here]

## Contact

[Your Contact Information]
