#!/usr/bin/env python3
"""
Demo script to test the file selection features
"""

import os
import sys
import pandas as pd
import glob
from datetime import datetime


def main():
    print("RF Data File Selection Demo")
    print("=" * 40)

    # Check if saved_data directory exists
    saved_data_dir = "./saved_data"
    if not os.path.exists(saved_data_dir):
        print(f"Error: {saved_data_dir} directory not found!")
        return

    # Load all CSV files
    csv_files = glob.glob(os.path.join(saved_data_dir, "*.csv"))
    if not csv_files:
        print("No CSV files found in saved_data directory!")
        return

    print(f"\nFound {len(csv_files)} data files:")
    print("-" * 40)

    data_files = []
    for i, file_path in enumerate(csv_files):
        try:
            df = pd.read_csv(file_path)
            filename = os.path.basename(file_path)

            # Extract device name
            if "(" in filename and ")" in filename:
                device_name = filename.split("(")[1].split(")")[0]
                df["device"] = device_name
            else:
                df["device"] = filename.replace(".csv", "").replace(
                    "spectrum_data_", ""
                )

            df["source_file"] = filename
            data_files.append(df)

            # Display file info
            duration_ms = df["timestamp"].max() - df["timestamp"].min()
            duration_s = duration_ms / 1000

            print(f"{i+1:2d}. {filename}")
            print(f"    Device: {df['device'].iloc[0]}")
            print(f"    Records: {len(df)}")
            print(f"    Duration: {duration_s:.1f} seconds")
            print(
                f"    Time range: {df['timestamp'].min()} to {df['timestamp'].max()} ms"
            )
            print()

        except Exception as e:
            print(f"Error loading {filename}: {e}")

    if data_files:
        # Show device summary
        all_devices = set()
        total_records = 0

        for df in data_files:
            all_devices.add(df["device"].iloc[0])
            total_records += len(df)

        print(f"Summary:")
        print(f"- Total files: {len(data_files)}")
        print(f"- Total records: {total_records}")
        print(f"- Unique devices: {len(all_devices)}")
        print(f"- Devices: {', '.join(sorted(all_devices))}")

        # Demonstrate file selection simulation
        print(f"\nFile Selection Demo:")
        print(f"This demonstrates how the GUI allows you to:")
        print(f"1. Select specific files to analyze")
        print(f"2. See exactly which device data you're viewing")
        print(f"3. Get file information (records count, duration, device)")
        print(f"4. Choose between individual file analysis or combined view")

        print(f"\nKey improvements:")
        print(f"✓ File list with device names and record counts")
        print(f"✓ Multi-select capability with status display")
        print(f"✓ Clear identification of which data is being plotted")
        print(f"✓ Individual file view option")
        print(f"✓ File summary statistics")


if __name__ == "__main__":
    main()
