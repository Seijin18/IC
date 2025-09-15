#!/usr/bin/env python3
"""
Quick RF Data Visualizer
A simple script to quickly visualize RF spectrum data from saved CSV files.
"""

import os
import sys
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import argparse


def load_all_data(data_dir):
    """Load all CSV files from the data directory"""
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    all_data = []

    print(f"Loading data from {data_dir}...")

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            filename = os.path.basename(file_path)

            # Add metadata
            df["source_file"] = filename

            # Extract device name
            if "(" in filename and ")" in filename:
                device_name = filename.split("(")[1].split(")")[0]
                df["device"] = device_name
            else:
                df["device"] = filename.replace(".csv", "").replace(
                    "spectrum_data_", ""
                )

            all_data.append(df)
            print(f"  Loaded {len(df)} records from {filename}")

        except Exception as e:
            print(f"  Error loading {filename}: {e}")

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined = combined.sort_values("timestamp").reset_index(drop=True)
        print(f"Total: {len(combined)} records from {len(all_data)} files")
        return combined
    else:
        print("No valid data files found!")
        return None


def create_overview_heatmap(data, output_path=None):
    """Create a comprehensive heatmap of all data"""
    channel_cols = [col for col in data.columns if col.startswith("Ch")]
    channel_data = data[channel_cols].values
    timestamps = data["timestamp"].values

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10))

    # Custom colormap
    colors = [(0, 0, 0.8), (0, 0.8, 0), (0.8, 0.8, 0), (0.8, 0, 0)]
    cmap = LinearSegmentedColormap.from_list("spectrum_cmap", colors, N=256)

    # Plot heatmap
    im = ax.imshow(channel_data.T, aspect="auto", cmap=cmap, interpolation="none")

    # Formatting
    ax.set_title(
        "RF Spectrum Activity Over Time - Complete Dataset",
        fontsize=16,
        fontweight="bold",
    )
    ax.set_xlabel("Time Points", fontsize=12)
    ax.set_ylabel("Channel (2400 + channel MHz)", fontsize=12)

    # Y-axis ticks
    y_ticks = np.arange(0, len(channel_cols), 10)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{tick+1} ({2400+tick+1} MHz)" for tick in y_ticks])

    # X-axis ticks (show time progression)
    if len(timestamps) > 20:
        x_ticks = np.linspace(0, len(timestamps) - 1, 10, dtype=int)
        time_labels = [f"{timestamps[i]/1000:.0f}s" for i in x_ticks]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(time_labels, rotation=45)

    # WiFi channel markers
    wifi_channels = [1, 6, 11]
    for ch in wifi_channels:
        ax.axhline(y=ch - 1, color="white", linestyle="--", alpha=0.8, linewidth=2)
        ax.text(
            len(timestamps) * 0.98,
            ch - 1,
            f"WiFi Ch{ch}",
            color="white",
            fontweight="bold",
            ha="right",
            va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="black", alpha=0.7),
        )

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Activity Level", rotation=270, labelpad=15, fontsize=12)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Heatmap saved to {output_path}")

    plt.show()


def create_channel_comparison(data, channels=None, output_path=None):
    """Create time series comparison for specific channels"""
    if channels is None:
        channels = [1, 6, 11, 40, 80]  # Default channels including WiFi

    fig, axes = plt.subplots(len(channels), 1, figsize=(14, 8), sharex=True)
    if len(channels) == 1:
        axes = [axes]

    timestamps = data["timestamp"].values / 1000  # Convert to seconds

    for i, ch in enumerate(channels):
        col_name = f"Ch{ch}"
        if col_name in data.columns:
            channel_data = data[col_name].values
            axes[i].plot(
                timestamps,
                channel_data,
                linewidth=1,
                alpha=0.8,
                color=f"C{i}",
                label=f"Channel {ch}",
            )
            axes[i].set_ylabel(f"Ch{ch}\n({2400+ch} MHz)", fontsize=10)
            axes[i].grid(True, alpha=0.3)
            axes[i].set_ylim(0, max(channel_data) * 1.1 if max(channel_data) > 0 else 1)

            # Add statistics
            mean_val = np.mean(channel_data)
            max_val = np.max(channel_data)
            axes[i].text(
                0.02,
                0.95,
                f"Mean: {mean_val:.1f}, Max: {max_val}",
                transform=axes[i].transAxes,
                fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
            )

    axes[-1].set_xlabel("Time (seconds)", fontsize=12)
    plt.suptitle("RF Channel Activity Comparison", fontsize=14, fontweight="bold")
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Channel comparison saved to {output_path}")

    plt.show()


def create_device_summary(data, output_path=None):
    """Create summary statistics and comparison between devices"""
    devices = data["device"].unique()

    if len(devices) <= 1:
        print("Only one device found, skipping device comparison")
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Activity heatmap by device
    channel_cols = [col for col in data.columns if col.startswith("Ch")]

    ax = axes[0, 0]
    for i, device in enumerate(devices):
        device_data = data[data["device"] == device]
        if len(device_data) > 0:
            channel_data = device_data[channel_cols].values
            activity_mean = np.mean(channel_data, axis=0)
            ax.plot(
                range(1, len(channel_cols) + 1),
                activity_mean,
                label=device,
                linewidth=2,
                alpha=0.8,
            )

    ax.set_title("Average Activity by Channel and Device")
    ax.set_xlabel("Channel Number")
    ax.set_ylabel("Average Activity Level")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Total activity over time by device
    ax = axes[0, 1]
    for device in devices:
        device_data = data[data["device"] == device]
        if len(device_data) > 0:
            timestamps = device_data["timestamp"].values / 1000
            channel_data = device_data[channel_cols].values
            total_activity = np.sum(channel_data, axis=1)
            ax.plot(timestamps, total_activity, label=device, alpha=0.8, linewidth=1)

    ax.set_title("Total Activity Over Time by Device")
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Total Activity (All Channels)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Device activity distribution
    ax = axes[1, 0]
    activity_by_device = []
    device_names = []

    for device in devices:
        device_data = data[data["device"] == device]
        if len(device_data) > 0:
            channel_data = device_data[channel_cols].values
            total_activity = np.sum(channel_data)
            activity_by_device.append(total_activity)
            device_names.append(device)

    bars = ax.bar(device_names, activity_by_device, alpha=0.7)
    ax.set_title("Total Activity by Device")
    ax.set_ylabel("Total Activity")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    # Add value labels on bars
    for bar, value in zip(bars, activity_by_device):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{value:.0f}",
            ha="center",
            va="bottom",
        )

    # 4. Recording duration by device
    ax = axes[1, 1]
    durations = []

    for device in devices:
        device_data = data[data["device"] == device]
        if len(device_data) > 0:
            duration = (
                device_data["timestamp"].max() - device_data["timestamp"].min()
            ) / 1000
            durations.append(duration)
        else:
            durations.append(0)

    bars = ax.bar(device_names, durations, alpha=0.7, color="orange")
    ax.set_title("Recording Duration by Device")
    ax.set_ylabel("Duration (seconds)")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    # Add value labels
    for bar, value in zip(bars, durations):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{value:.1f}s",
            ha="center",
            va="bottom",
        )

    plt.suptitle("Device Comparison Summary", fontsize=16, fontweight="bold")
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Device summary saved to {output_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Quick RF Data Visualizer")
    parser.add_argument(
        "data_dir",
        nargs="?",
        default=os.path.join(os.path.dirname(__file__), "saved_data"),
        help="Directory containing CSV data files",
    )
    parser.add_argument("--output-dir", "-o", help="Directory to save output images")
    parser.add_argument(
        "--channels",
        "-c",
        default="1,6,11,40,80",
        help="Comma-separated list of channels for time series",
    )
    parser.add_argument(
        "--heatmap-only", action="store_true", help="Only generate heatmap"
    )
    parser.add_argument(
        "--no-show", action="store_true", help="Don't show plots, only save them"
    )

    args = parser.parse_args()

    # Check if data directory exists
    if not os.path.exists(args.data_dir):
        print(f"Error: Data directory '{args.data_dir}' not found!")
        print("Usage examples:")
        print("  python quick_visualizer.py")
        print("  python quick_visualizer.py /path/to/data")
        print("  python quick_visualizer.py --output-dir ./plots")
        return

    # Load data
    data = load_all_data(args.data_dir)
    if data is None:
        return

    # Set up output paths
    output_heatmap = None
    output_channels = None
    output_summary = None

    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        output_heatmap = os.path.join(args.output_dir, "rf_spectrum_heatmap.png")
        output_channels = os.path.join(args.output_dir, "rf_channel_comparison.png")
        output_summary = os.path.join(args.output_dir, "rf_device_summary.png")

    # Disable showing if requested
    if args.no_show:
        plt.ioff()

    # Generate visualizations
    print("\nGenerating heatmap...")
    create_overview_heatmap(data, output_heatmap)

    if not args.heatmap_only:
        print("\nGenerating channel comparison...")
        channels = [int(ch.strip()) for ch in args.channels.split(",")]
        create_channel_comparison(data, channels, output_channels)

        print("\nGenerating device summary...")
        create_device_summary(data, output_summary)

    print("\nVisualization complete!")

    if args.output_dir:
        print(f"Images saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
