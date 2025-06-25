# Simple Script to Generate Test Data for Spectrum Visualizer
# Run this to create sample data if you haven't collected real data yet

import numpy as np
import pandas as pd
import os
import time


def generate_test_data(num_samples=60):
    """Generate simulated spectrum data to test visualization"""
    # Create dataframe structure
    columns = ["Timestamp"] + [f"Ch{i}" for i in range(126)]
    df = pd.DataFrame(columns=columns)

    # Generate timestamps (seconds)
    timestamps = list(range(num_samples))

    # Generate data for each timestamp
    for t in timestamps:
        # Start with baseline random noise (0-5%)
        channel_data = np.random.randint(0, 5, 126)

        # Add some patterns

        # 1. Wi-Fi channel 1 (channels 1-13)
        if t % 3 == 0:  # active every 3 seconds
            channel_data[1:14] += np.random.randint(10, 40, 13)

        # 2. Wi-Fi channel 6 (channels 26-38)
        channel_data[26:39] += np.random.randint(5, 30, 13)

        # 3. Wi-Fi channel 11 (channels 51-63)
        if t % 5 < 3:  # active for 3 out of every 5 seconds
            channel_data[51:64] += np.random.randint(15, 50, 13)

        # 4. Add a moving interference source
        center = (t % 100) + 10
        if center < 126:
            width = 5
            start = max(0, center - width)
            end = min(126, center + width)
            channel_data[start:end] += np.random.randint(40, 80, end - start)

        # Ensure no values exceed 100%
        channel_data = np.clip(channel_data, 0, 100)

        # Add row to dataframe
        row_data = [t] + list(channel_data)
        df.loc[t] = row_data

    return df


def save_test_data(file_path="test_spectrum_data.csv", num_samples=60):
    """Generate and save test data to CSV file"""
    df = generate_test_data(num_samples)
    df.to_csv(file_path, index=False)
    print(f"Test data saved to {file_path}")
    print(f"Generated {num_samples} samples across 126 channels")

    # Print usage instructions
    print("\nTo visualize this data, run:")
    print(f"python spectrum_visualizer.py {file_path}")
    print("For animated visualization:")
    print(f"python spectrum_visualizer.py {file_path} --animate")
    print("To save the visualization:")
    print(f"python spectrum_visualizer.py {file_path} --output spectrum.png")
    print("To analyze the spectrum data:")
    print(f"python spectrum_visualizer.py {file_path} --analyze")


if __name__ == "__main__":
    save_test_data(num_samples=120)  # Generate 2 minutes of data at 1 sample/second
