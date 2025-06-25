import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.animation as animation
import argparse
import os
from datetime import datetime, timedelta
import time
import threading
import sys

# Import optional modules with fallbacks
try:
    import matplotlib.patheffects as path_effects
except ImportError:
    path_effects = None
    print(
        "Warning: matplotlib.patheffects not available, some visual enhancements will be disabled"
    )

try:
    import serial
except ImportError:
    serial = None
    print("Warning: pyserial not available, serial port functionality will be disabled")


def read_csv_file(file_path):
    """Read the spectrum data CSV file"""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None


def create_heatmap(data, title="RF Spectrum Activity Over Time"):
    """Create a static heatmap visualization of spectrum data"""
    # Extract timestamp and channel data
    timestamp_col = "timestamp" if "timestamp" in data.columns else "Timestamp"
    timestamps = data[timestamp_col].values
    channel_data = data.drop(columns=[timestamp_col]).values

    # Create time labels (convert milliseconds to HH:MM:SS format if needed)
    time_labels = []
    is_milliseconds = timestamps[-1] > 100000  # Heuristic to detect if in milliseconds

    if is_milliseconds:
        # Convert milliseconds to seconds
        timestamps_sec = timestamps / 1000
        start_time = datetime.now() - timedelta(seconds=float(timestamps_sec[-1]))
        for t in timestamps_sec:
            time_str = (start_time + timedelta(seconds=float(t))).strftime("%H:%M:%S")
            time_labels.append(time_str)
    else:
        # Assume timestamps are already in seconds
        start_time = datetime.now() - timedelta(seconds=float(timestamps[-1]))
        for t in timestamps:
            time_str = (start_time + timedelta(seconds=float(t))).strftime("%H:%M:%S")
            time_labels.append(time_str)

    # Create figure
    fig = plt.figure(figsize=(14, 8))

    # Create custom colormap: blue (low) -> green -> yellow -> red (high)
    colors = [(0, 0, 0.8), (0, 0.8, 0), (0.8, 0.8, 0), (0.8, 0, 0)]
    cmap = LinearSegmentedColormap.from_list("spectrum_cmap", colors, N=256)

    # Plot heatmap
    im = plt.imshow(channel_data.T, aspect="auto", cmap=cmap, interpolation="none")

    # Set labels and title with improved positioning and styling
    plt.title(title, fontsize=18, fontweight="bold", pad=15)
    plt.xlabel("Time", fontsize=14, fontweight="bold", labelpad=12)
    plt.ylabel(
        "Channel Number (2400 + channel MHz)",
        fontsize=14,
        fontweight="bold",
        labelpad=15,
        rotation=90,
    )

    # Add grid for better readability
    plt.grid(False)

    # Configure colorbar with improved positioning and formatting
    cbar = plt.colorbar(im, label="Activity (%)", pad=0.02, fraction=0.046)
    cbar.ax.tick_params(labelsize=12)
    cbar.set_label(
        "Activity (%)", size=14, weight="bold", labelpad=12, rotation=270, va="bottom"
    )

    # Set y-axis ticks to show channel numbers with better formatting
    y_ticks = np.arange(0, 126, 10)
    plt.yticks(y_ticks, [f"{tick} ({2400+tick} MHz)" for tick in y_ticks], fontsize=12)

    # Add horizontal lines at Wi-Fi channels for better context
    wifi_channels = [1, 6, 11]  # Standard WiFi channels
    wifi_freqs = [2412, 2437, 2462]  # Corresponding center frequencies
    for i, freq in enumerate(wifi_freqs):
        ch = freq - 2400
        plt.axhline(y=ch, color="white", linestyle="--", alpha=0.5, linewidth=1)

        # Calculate a better position for the Wi-Fi channel labels
        x_pos = len(timestamps) - 1  # Position at the last data point

        try:
            # Try to use path effects for better text visibility
            plt.text(
                x_pos - len(timestamps) * 0.02,
                ch,
                f"Wi-Fi {wifi_channels[i]}",
                color="white",
                fontsize=10,
                va="center",
                ha="right",
                fontweight="bold",
                path_effects=[path_effects.withStroke(linewidth=2, foreground="black")],
            )
        except Exception:
            # Fallback if path_effects isn't available
            plt.text(
                x_pos - len(timestamps) * 0.02,
                ch,
                f"Wi-Fi {wifi_channels[i]}",
                color="white",
                fontsize=10,
                va="center",
                ha="right",
                fontweight="bold",
                bbox=dict(facecolor="black", alpha=0.4, pad=1),
            )

    # Set x-axis ticks with improved positioning and formatting to prevent overlap
    if len(timestamps) > 15:
        # For many timestamps, show fewer labels to prevent crowding
        num_ticks = min(8, len(timestamps))
        x_tick_indices = np.linspace(0, len(timestamps) - 1, num_ticks, dtype=int)
        plt.xticks(
            x_tick_indices,
            [time_labels[i] for i in x_tick_indices],
            rotation=45,
            fontsize=12,
            ha="right",
        )
    else:
        # For fewer timestamps, we can show more labels
        step = max(
            1, len(timestamps) // 10
        )  # Ensure we don't have more than ~10 labels
        x_tick_indices = range(0, len(timestamps), step)
        plt.xticks(
            x_tick_indices,
            [time_labels[i] for i in x_tick_indices],
            rotation=45,
            fontsize=12,
            ha="right",
        )

    # Better axis styling
    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)
    plt.gca().spines["bottom"].set_linewidth(1.5)
    plt.gca().spines["left"].set_linewidth(1.5)
    plt.gca().tick_params(width=1.5, length=6)

    # Add watermark in a less intrusive position
    plt.figtext(
        0.99,
        0.01,
        "RF Spectrum Analyzer",
        ha="right",
        va="bottom",
        alpha=0.2,
        fontsize=9,
        fontstyle="italic",
    )

    # Adjust layout with better margins for improved label visibility
    plt.tight_layout(pad=1.2, h_pad=1.5, w_pad=1.5)

    # Adjust bottom margin to ensure x-axis labels are fully visible
    plt.subplots_adjust(bottom=0.15)

    return fig


def create_animated_heatmap(data, output_file=None, interval=200):
    """Create an animated heatmap showing how the spectrum changes over time"""
    # Extract channel data (excluding timestamp column)
    channel_data = data.iloc[:, 1:].values
    num_frames = len(channel_data)

    # Setup figure and initial heatmap
    fig, ax = plt.subplots(figsize=(14, 8))

    # Create custom colormap: blue (low) -> green -> yellow -> red (high)
    colors = [(0, 0, 0.8), (0, 0.8, 0), (0.8, 0.8, 0), (0.8, 0, 0)]
    cmap = LinearSegmentedColormap.from_list("spectrum_cmap", colors, N=256)

    # Initial empty heatmap
    heatmap = ax.imshow(
        np.zeros((126, 126)),
        aspect="auto",
        cmap=cmap,
        interpolation="none",
        vmin=0,
        vmax=100,
    )

    # Add colorbar with better positioning and styling
    cbar = plt.colorbar(heatmap, ax=ax, label="Activity (%)", pad=0.02, fraction=0.046)
    cbar.ax.tick_params(labelsize=12)
    cbar.set_label(
        "Activity (%)", size=14, weight="bold", labelpad=12, rotation=270, va="bottom"
    )

    # Configure axes with improved styling and positioning
    ax.set_title(
        "RF Spectrum Activity Over Time", fontsize=18, fontweight="bold", pad=15
    )
    ax.set_xlabel("Time", fontsize=14, fontweight="bold", labelpad=12)
    ax.set_ylabel(
        "Channel Number (2400 + channel MHz)",
        fontsize=14,
        fontweight="bold",
        labelpad=15,
        rotation=90,
    )

    # Set y-axis ticks with better formatting
    y_ticks = np.arange(0, 126, 10)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{tick} ({2400+tick} MHz)" for tick in y_ticks], fontsize=12)

    # Add horizontal lines at Wi-Fi channels for better context
    wifi_channels = [1, 6, 11]  # Standard WiFi channels
    wifi_freqs = [2412, 2437, 2462]  # Corresponding center frequencies
    for i, freq in enumerate(wifi_freqs):
        ch = freq - 2400
        ax.axhline(y=ch, color="white", linestyle="--", alpha=0.5, linewidth=1)

        # Better positioning for the Wi-Fi channel labels
        x_pos = 120  # Position near the right edge but not at the very edge

        try:
            # Try to use path effects for better text visibility with improved positioning
            ax.text(
                x_pos,
                ch,
                f"Wi-Fi {wifi_channels[i]}",
                color="white",
                fontsize=10,
                va="center",
                ha="right",
                fontweight="bold",
                path_effects=[path_effects.withStroke(linewidth=2, foreground="black")],
            )
        except Exception:
            # Fallback if path_effects isn't available
            ax.text(
                x_pos,
                ch,
                f"Wi-Fi {wifi_channels[i]}",
                color="white",
                fontsize=10,
                va="center",
                ha="right",
                fontweight="bold",
                bbox=dict(facecolor="black", alpha=0.4, pad=1),
            )

    # Better axis styling
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_linewidth(1.5)
    ax.spines["left"].set_linewidth(1.5)
    ax.tick_params(width=1.5, length=6)

    # Add a background grid for better channel visualization
    ax.grid(False)

    # Setup for animation - check both capitalization versions of 'timestamp'
    timestamp_col = "timestamp" if "timestamp" in data.columns else "Timestamp"
    timestamps = data[timestamp_col].values

    # Convert numpy.int64 to Python int for compatibility with timedelta
    is_milliseconds = timestamps[-1] > 100000  # Heuristic to detect if in milliseconds

    if is_milliseconds:
        # Convert milliseconds to seconds first
        last_timestamp_sec = float(timestamps[-1]) / 1000
        start_time = datetime.now() - timedelta(seconds=last_timestamp_sec)
    else:
        # Use timestamps directly as seconds
        start_time = datetime.now() - timedelta(seconds=float(timestamps[-1]))

    history = np.zeros((126, 126))  # History buffer to show evolution over time

    def animate(frame):
        nonlocal history

        # Shift history to the left
        history = np.roll(history, -1, axis=1)

        # Add new data column to right edge
        history[:, -1] = channel_data[frame % num_frames]

        # Update heatmap data with enhanced visualization
        heatmap.set_array(history)

        # Update time label with better formatting
        current_timestamp = timestamps[frame % num_frames]
        if is_milliseconds:
            current_time_sec = float(current_timestamp) / 1000
        else:
            current_time_sec = float(current_timestamp)

        current_time = (start_time + timedelta(seconds=current_time_sec)).strftime(
            "%H:%M:%S"
        )

        # Add time info to title with frame counter for better context
        progress = int(
            (frame % num_frames) / num_frames * 20
        )  # Create a progress indicator
        progress_bar = "█" * progress + "░" * (20 - progress)

        ax.set_title(
            f"RF Spectrum Activity - Time: {current_time}  [{progress_bar}]",
            fontsize=18,
            fontweight="bold",
        )

        # Add real-time frame counter with better positioning
        if hasattr(animate, "text"):
            animate.text.remove()
        animate.text = ax.text(
            0.98,
            0.02,
            f"Frame {frame % num_frames + 1}/{num_frames}",
            transform=ax.transAxes,
            ha="right",
            fontsize=10,
            alpha=0.7,
            bbox=dict(
                facecolor="white",
                alpha=0.7,
                pad=3,
                edgecolor="gray",
                boxstyle="round,pad=0.5",
            ),
        )

        return heatmap, animate.text

    # Add watermark for the visualization in a less intrusive position
    fig.text(
        0.99,
        0.01,
        "RF Spectrum Analyzer",
        ha="right",
        va="bottom",
        alpha=0.2,
        fontsize=9,
        fontstyle="italic",
        transform=fig.transFigure,
    )

    # Add timestamp to know when the visualization was created
    current_datetime = datetime.now().strftime("%Y-%m-%d")
    fig.text(
        0.01,
        0.01,
        f"Generated: {current_datetime}",
        ha="left",
        va="bottom",
        alpha=0.4,
        fontsize=8,
        transform=fig.transFigure,
    )

    # Better layout handling for animation with improved margins
    plt.tight_layout(pad=1.2, h_pad=1.5, w_pad=1.5)

    # Adjust bottom margin to ensure x-axis labels are fully visible
    plt.subplots_adjust(bottom=0.15)

    # Initialize text attribute for animate function
    animate.text = ax.text(0.99, 0.01, "", transform=ax.transAxes)

    # Create smoother animation with improved parameters
    ani = animation.FuncAnimation(
        fig,
        animate,
        frames=num_frames,
        interval=interval,
        blit=True,
        repeat=True,
        repeat_delay=1000,
    )  # Add a 1-second delay between repeats

    # Save animation with better quality if output file specified
    if output_file:
        if output_file.endswith(".mp4"):
            try:
                # Try higher quality MP4 output with FFMpegWriter
                writer = animation.FFMpegWriter(fps=10, bitrate=1800)
                ani.save(output_file, writer=writer)
                print(f"Saved MP4 animation to {output_file}")
            except Exception as e:
                print(f"Warning: Couldn't save as MP4: {e}")
                print("Falling back to GIF format...")
                # Fallback to GIF if MP4 fails
                gif_output = output_file.replace(".mp4", ".gif")
                ani.save(gif_output, writer="pillow", fps=8, dpi=120)
                print(f"Saved GIF animation to {gif_output}")
        else:
            # Default to pillow for GIF with better quality
            try:
                ani.save(output_file, writer="pillow", fps=8, dpi=120)
                print(f"Saved animation to {output_file}")
            except Exception as e:
                print(f"Error saving animation: {e}")

    return fig, ani


def analyze_spectrum(data):
    """Analyze spectrum data and print statistics"""
    # Get timestamp column name
    timestamp_col = "timestamp" if "timestamp" in data.columns else "Timestamp"

    # Get channel data (excluding timestamp column)
    channel_data = data.drop(columns=[timestamp_col])

    # Calculate statistics
    avg_activity = channel_data.mean().mean()
    peak_channel = channel_data.mean().idxmax()

    # Get the channel number from the column name
    if peak_channel.startswith("Ch"):
        peak_channel_num = int(peak_channel[2:])
    elif peak_channel.startswith("ch"):
        peak_channel_num = int(peak_channel[2:])
    else:
        try:
            peak_channel_num = int(peak_channel)
        except:
            peak_channel_num = 0

    peak_channel_freq = 2400 + peak_channel_num

    # Get most active channels (average > 10%)
    active_channels = channel_data.mean()[channel_data.mean() > 10]

    print("\n===== Spectrum Analysis =====")
    print(f"Average activity across all channels: {avg_activity:.2f}%")
    print(
        f"Peak activity channel: {peak_channel} ({peak_channel_freq} MHz) with {channel_data.mean()[peak_channel]:.2f}% average activity"
    )

    print("\nMost Active Channels:")
    for channel, activity in active_channels.items():
        channel_num = int(channel.replace("Ch", ""))
        freq = 2400 + channel_num
        print(f"  {channel} ({freq} MHz): {activity:.2f}% average activity")

    # Identify common Wi-Fi channels
    wifi_channels = {
        1: range(1, 14),  # 2401-2413 MHz
        6: range(26, 39),  # 2426-2438 MHz
        11: range(51, 64),  # 2451-2463 MHz
    }

    print("\nWi-Fi Channel Activity:")
    for wifi_ch, ch_range in wifi_channels.items():
        ch_cols = [f"Ch{ch}" for ch in ch_range if f"Ch{ch}" in channel_data.columns]
        if ch_cols:
            avg = channel_data[ch_cols].mean().mean()
            print(f"  Wi-Fi Channel {wifi_ch}: {avg:.2f}% average activity")


def read_from_serial(port, baud_rate=115200, timeout=10, max_samples=None):
    """Read spectrum data directly from the serial port"""
    try:
        print(f"Opening serial port {port} at {baud_rate} baud...")
        ser = serial.Serial(port, baud_rate, timeout=1)
        time.sleep(2)  # Allow time for connection to establish

        print("Serial port opened. Waiting for data...")
        print("Press Ctrl+C to stop data collection")

        # Prepare to collect data
        data = []
        header = None
        start_time = time.time()
        sample_count = 0

        # Clear any initial data
        ser.flushInput()

        # Send 'v' command to activate CSV mode
        ser.write(b"v")
        time.sleep(0.5)

        while True:
            if max_samples and sample_count >= max_samples:
                print(f"\nReached maximum sample count ({max_samples})")
                break

            if time.time() - start_time > timeout and not data:
                print(f"\nTimeout reached ({timeout}s) without receiving data")
                break

            line = ser.readline().decode("utf-8").strip()

            if not line:
                continue

            # Check if this is the header line
            if line.startswith("timestamp") and not header:
                header = line.split(",")
                print("CSV header received. Starting data collection...")
                continue

            # Process data lines
            if header and "," in line:
                try:
                    values = line.split(",")
                    # Ensure we have the right number of values
                    if len(values) == len(header):
                        data.append(values)
                        sample_count += 1

                        # Show progress
                        if sample_count % 10 == 0:
                            print(f"\rCollected {sample_count} samples...", end="")
                            sys.stdout.flush()
                except Exception as e:
                    print(f"\nError parsing line: {e}")
                    print(f"Line: {line}")

        # Send 'v' command to deactivate CSV mode
        ser.write(b"v")

        # Close the serial port
        ser.close()
        print("\nSerial port closed.")

        if not data:
            print("No data was collected.")
            return None

        # Convert to pandas DataFrame
        df = pd.DataFrame(data, columns=header)

        # Convert values from strings to appropriate types
        df["timestamp"] = pd.to_numeric(df["timestamp"])
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col])

        print(
            f"Successfully collected {len(df)} samples with {len(df.columns)-1} channels."
        )
        return df

    except serial.SerialException as e:
        print(f"Serial port error: {e}")
        return None
    except KeyboardInterrupt:
        print("\nData collection stopped by user.")
        try:
            ser.write(b"v")  # Try to deactivate CSV mode
            ser.close()
        except:
            pass

        if data:
            # Convert to pandas DataFrame
            df = pd.DataFrame(data, columns=header)

            # Convert values from strings to appropriate types
            df["timestamp"] = pd.to_numeric(df["timestamp"])
            for col in df.columns[1:]:
                df[col] = pd.to_numeric(df[col])

            print(
                f"Successfully collected {len(df)} samples with {len(df.columns)-1} channels."
            )
            return df
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Visualize NRF24L01 spectrum data from CSV file or serial port"
    )

    # Create mutually exclusive group for file vs serial
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--file", help="Path to the CSV file with spectrum data")
    source_group.add_argument(
        "--serial",
        help="Serial port to read data from (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux)",
    )

    # Other arguments
    parser.add_argument(
        "--baud", type=int, default=115200, help="Baud rate for serial communication"
    )
    parser.add_argument(
        "--samples", type=int, help="Number of samples to collect from serial port"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout for serial data collection in seconds",
    )
    parser.add_argument(
        "--animate", action="store_true", help="Create animated visualization"
    )
    parser.add_argument(
        "--output",
        help="Save visualization to file (PNG for static, GIF or MP4 for animation)",
    )
    parser.add_argument("--analyze", action="store_true", help="Analyze spectrum data")
    parser.add_argument("--save-csv", help="Save collected serial data to CSV file")
    parser.add_argument(
        "--interval",
        type=int,
        default=200,
        help="Animation frame interval in milliseconds (smaller = faster)",
    )

    args = parser.parse_args()

    # Read the data
    if args.file:
        data = read_csv_file(args.file)
        if data is None:
            return

        print(f"Loaded data from {args.file}")

    elif args.serial:
        data = read_from_serial(args.serial, args.baud, args.timeout, args.samples)
        if data is None:
            return

        print(f"Successfully read data from {args.serial}")

        # Save collected data to CSV if requested
        if args.save_csv:
            data.to_csv(args.save_csv, index=False)
            print(f"Data saved to {args.save_csv}")

    # Print basic info
    print(f"Total records: {len(data)}")
    timestamp_col = "timestamp" if "timestamp" in data.columns else "Timestamp"
    print(
        f"Time span: {data[timestamp_col].min()} to {data[timestamp_col].max()} milliseconds"
    )

    # Analyze data if requested
    if args.analyze:
        analyze_spectrum(data)

    # Create visualization
    if args.animate:
        fig, ani = create_animated_heatmap(data, args.output, interval=args.interval)
        plt.show()
    else:
        fig = create_heatmap(data)
        if args.output:
            fig.savefig(args.output)
        plt.show()


if __name__ == "__main__":
    main()
