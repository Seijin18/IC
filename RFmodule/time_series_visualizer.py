import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
import os
import glob
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class RFTimeSeriesVisualizer:
    def __init__(self):
        self.data_files = []
        self.combined_data = None
        self.fig = None
        self.ax = None
        self.slider = None
        self.time_window = 100  # Number of time points to show
        self.current_time_index = 0

    def load_data_files(self, directory_path):
        """Load all CSV files from the saved_data directory"""
        csv_files = glob.glob(os.path.join(directory_path, "*.csv"))
        self.data_files = []

        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)
                # Add filename and metadata
                filename = os.path.basename(file_path)
                df["source_file"] = filename

                # Extract device name from filename if it contains parentheses
                if "(" in filename and ")" in filename:
                    device_name = filename.split("(")[1].split(")")[0]
                    df["device"] = device_name
                else:
                    df["device"] = "unknown"

                self.data_files.append(df)
                print(f"Loaded {len(df)} records from {filename}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

        if self.data_files:
            # Combine all data
            self.combined_data = pd.concat(self.data_files, ignore_index=True)
            # Sort by timestamp
            self.combined_data = self.combined_data.sort_values(
                "timestamp"
            ).reset_index(drop=True)
            print(f"Total combined records: {len(self.combined_data)}")
        else:
            print("No data files loaded")

    def create_animated_heatmap(self):
        """Create an animated heatmap showing RF spectrum over time"""
        if self.combined_data is None:
            print("No data loaded. Please load data files first.")
            return

        # Extract channel data (excluding metadata columns)
        channel_cols = [
            col for col in self.combined_data.columns if col.startswith("Ch")
        ]
        channel_data = self.combined_data[channel_cols].values
        timestamps = self.combined_data["timestamp"].values

        # Create figure
        self.fig, self.ax = plt.subplots(figsize=(14, 8))
        plt.subplots_adjust(bottom=0.2)

        # Create custom colormap
        colors = [(0, 0, 0.8), (0, 0.8, 0), (0.8, 0.8, 0), (0.8, 0, 0)]
        cmap = LinearSegmentedColormap.from_list("spectrum_cmap", colors, N=256)

        # Initial plot
        self.im = self.ax.imshow(
            channel_data[: self.time_window].T,
            aspect="auto",
            cmap=cmap,
            interpolation="none",
        )

        # Configure plot
        self.ax.set_title(
            "RF Spectrum Activity Over Time", fontsize=16, fontweight="bold"
        )
        self.ax.set_xlabel("Time Points", fontsize=12)
        self.ax.set_ylabel("Channel (2400 + channel MHz)", fontsize=12)

        # Set y-axis ticks
        y_ticks = np.arange(0, len(channel_cols), 10)
        self.ax.set_yticks(y_ticks)
        self.ax.set_yticklabels([f"{tick+1} ({2400+tick+1} MHz)" for tick in y_ticks])

        # Add colorbar
        cbar = plt.colorbar(self.im, ax=self.ax)
        cbar.set_label("Activity Level", rotation=270, labelpad=15)

        # Add WiFi channel markers
        wifi_channels = [1, 6, 11]
        for ch in wifi_channels:
            self.ax.axhline(
                y=ch - 1, color="white", linestyle="--", alpha=0.7, linewidth=1
            )
            self.ax.text(
                self.time_window - 5,
                ch - 1,
                f"WiFi {ch}",
                color="white",
                fontweight="bold",
                va="center",
            )

        # Create slider for time navigation
        ax_slider = plt.axes([0.1, 0.05, 0.8, 0.03])
        self.slider = Slider(
            ax_slider,
            "Time Position",
            0,
            max(0, len(channel_data) - self.time_window),
            valinit=0,
            valfmt="%d",
        )
        self.slider.on_changed(self.update_plot)

        plt.show()

    def update_plot(self, val):
        """Update the heatmap based on slider position"""
        if self.combined_data is None:
            return

        channel_cols = [
            col for col in self.combined_data.columns if col.startswith("Ch")
        ]
        channel_data = self.combined_data[channel_cols].values

        start_idx = int(self.slider.val)
        end_idx = min(start_idx + self.time_window, len(channel_data))

        # Update image data
        self.im.set_array(channel_data[start_idx:end_idx].T)
        self.im.set_extent([start_idx, end_idx - 1, 0, len(channel_cols)])

        # Update title with timestamp info
        start_time = self.combined_data.iloc[start_idx]["timestamp"]
        end_time = self.combined_data.iloc[end_idx - 1]["timestamp"]
        self.ax.set_title(
            f"RF Spectrum Activity - Time: {start_time/1000:.1f}s to {end_time/1000:.1f}s",
            fontsize=16,
            fontweight="bold",
        )

        self.fig.canvas.draw()

    def create_channel_time_series(self, channels=None):
        """Create time series plots for specific channels"""
        if self.combined_data is None:
            print("No data loaded. Please load data files first.")
            return

        if channels is None:
            # Default to WiFi channels and some others
            channels = [1, 6, 11, 40, 80]

        fig, axes = plt.subplots(len(channels), 1, figsize=(12, 8), sharex=True)
        if len(channels) == 1:
            axes = [axes]

        timestamps = self.combined_data["timestamp"].values / 1000  # Convert to seconds

        for i, ch in enumerate(channels):
            col_name = f"Ch{ch}"
            if col_name in self.combined_data.columns:
                data = self.combined_data[col_name].values
                axes[i].plot(timestamps, data, linewidth=1, alpha=0.7)
                axes[i].set_ylabel(f"Ch{ch}\n({2400+ch} MHz)", fontsize=10)
                axes[i].grid(True, alpha=0.3)
                axes[i].set_ylim(0, max(data) * 1.1 if max(data) > 0 else 1)

        axes[-1].set_xlabel("Time (seconds)", fontsize=12)
        plt.suptitle("RF Channel Activity Over Time", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.show()

    def create_device_comparison(self):
        """Create comparison plots between different devices"""
        if self.combined_data is None:
            print("No data loaded. Please load data files first.")
            return

        devices = self.combined_data["device"].unique()
        if len(devices) <= 1:
            print("Need multiple devices for comparison")
            return

        fig, axes = plt.subplots(len(devices), 1, figsize=(14, 10), sharex=True)
        if len(devices) == 1:
            axes = [axes]

        channel_cols = [
            col for col in self.combined_data.columns if col.startswith("Ch")
        ]

        for i, device in enumerate(devices):
            device_data = self.combined_data[self.combined_data["device"] == device]
            channel_data = device_data[channel_cols].values

            if len(channel_data) > 0:
                # Create heatmap for this device
                im = axes[i].imshow(
                    channel_data.T, aspect="auto", cmap="hot", interpolation="none"
                )
                axes[i].set_title(f"Device: {device}", fontweight="bold")
                axes[i].set_ylabel("Channel")

                # Set y-axis ticks
                y_ticks = np.arange(0, len(channel_cols), 20)
                axes[i].set_yticks(y_ticks)
                axes[i].set_yticklabels([f"{tick+1}" for tick in y_ticks])

        axes[-1].set_xlabel("Time Points")
        plt.suptitle(
            "RF Spectrum Comparison Between Devices", fontsize=16, fontweight="bold"
        )
        plt.tight_layout()
        plt.show()


class RFVisualizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RF Spectrum Time Series Visualizer")
        self.root.geometry("800x600")

        self.visualizer = RFTimeSeriesVisualizer()
        self.data_loaded = False

        self.setup_gui()

    def setup_gui(self):
        """Setup the GUI elements"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Data loading section
        load_frame = ttk.LabelFrame(main_frame, text="Data Loading", padding="10")
        load_frame.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        ttk.Button(
            load_frame, text="Load Data Directory", command=self.load_data_directory
        ).grid(row=0, column=0, padx=(0, 10))

        self.status_label = ttk.Label(load_frame, text="No data loaded")
        self.status_label.grid(row=0, column=1, padx=(10, 0))

        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        ttk.Label(file_frame, text="Select files to visualize:").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )

        # Create frame for file list
        list_frame = ttk.Frame(file_frame)
        list_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )

        # Listbox with scrollbar
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=6)
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.file_listbox.yview
        )
        self.file_listbox.configure(yscrollcommand=scrollbar.set)

        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        list_frame.columnconfigure(0, weight=1)

        # Selection buttons
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W)

        ttk.Button(button_frame, text="Select All", command=self.select_all_files).grid(
            row=0, column=0, padx=(0, 5)
        )
        ttk.Button(
            button_frame, text="Clear Selection", command=self.clear_file_selection
        ).grid(row=0, column=1, padx=5)
        ttk.Button(
            button_frame, text="Select by Device", command=self.select_by_device
        ).grid(row=0, column=2, padx=5)

        # Current selection label
        self.selection_label = ttk.Label(file_frame, text="No files selected")
        self.selection_label.grid(
            row=3, column=0, columnspan=3, sticky=tk.W, pady=(5, 0)
        )

        # Visualization options
        viz_frame = ttk.LabelFrame(
            main_frame, text="Visualization Options", padding="10"
        )
        viz_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(
            viz_frame, text="Animated Heatmap", command=self.create_animated_heatmap
        ).grid(row=0, column=0, padx=5, pady=5)

        ttk.Button(
            viz_frame, text="Channel Time Series", command=self.create_time_series
        ).grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(
            viz_frame, text="Device Comparison", command=self.create_device_comparison
        ).grid(row=0, column=2, padx=5, pady=5)

        ttk.Button(
            viz_frame,
            text="Individual File View",
            command=self.create_individual_file_view,
        ).grid(row=1, column=0, padx=5, pady=5)

        ttk.Button(
            viz_frame, text="File Summary", command=self.create_file_summary
        ).grid(row=1, column=1, padx=5, pady=5)

        # Configuration options
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(
            row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        ttk.Label(config_frame, text="Time Window Size:").grid(
            row=0, column=0, padx=(0, 5)
        )
        self.time_window_var = tk.StringVar(value="100")
        time_window_entry = ttk.Entry(
            config_frame, textvariable=self.time_window_var, width=10
        )
        time_window_entry.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(config_frame, text="Channels to plot:").grid(
            row=0, column=2, padx=(0, 5)
        )
        self.channels_var = tk.StringVar(value="1,6,11,40,80")
        channels_entry = ttk.Entry(
            config_frame, textvariable=self.channels_var, width=15
        )
        channels_entry.grid(row=0, column=3)

        # Info text
        info_text = tk.Text(main_frame, height=12, width=80)
        info_text.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0)
        )

        scrollbar_info = ttk.Scrollbar(
            main_frame, orient="vertical", command=info_text.yview
        )
        scrollbar_info.grid(row=4, column=2, sticky=(tk.N, tk.S))
        info_text.configure(yscrollcommand=scrollbar_info.set)

        self.info_text = info_text

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        self.add_info_text()

    def add_info_text(self):
        """Add informational text to the GUI"""
        info = """RF Spectrum Time Series Visualizer

This tool allows you to visualize RF spectrum data collected over time from multiple sources.

Features:
• Animated Heatmap: Shows RF activity across all channels over time with a slider for navigation
• Channel Time Series: Plots specific channels as line graphs over time
• Device Comparison: Compares RF patterns between different devices

Usage:
1. Click 'Load Data Directory' to select the folder containing your CSV files
2. Configure visualization parameters if needed
3. Choose a visualization type

Data Format:
- CSV files with timestamp and channel data (Ch1, Ch2, ..., Ch126)
- Files can be named with device identifiers in parentheses: (device) filename.csv

Tips:
- Use smaller time window sizes for better performance with large datasets
- WiFi channels (1, 6, 11) are marked on heatmaps for reference
- Time series plots work best with 3-10 channels selected
"""
        self.info_text.insert(tk.END, info)
        self.info_text.config(state=tk.DISABLED)

    def load_data_directory(self):
        """Load data from selected directory"""
        directory = filedialog.askdirectory(title="Select Data Directory")
        if directory:
            try:
                self.visualizer.load_data_files(directory)
                if self.visualizer.combined_data is not None:
                    self.data_loaded = True
                    num_records = len(self.visualizer.combined_data)
                    num_devices = len(self.visualizer.combined_data["device"].unique())
                    self.status_label.config(
                        text=f"Loaded {num_records} records from {num_devices} devices"
                    )
                    self.populate_file_list()
                else:
                    self.status_label.config(text="No valid data files found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load data: {e}")

    def populate_file_list(self):
        """Populate the file selection listbox"""
        self.file_listbox.delete(0, tk.END)
        if hasattr(self.visualizer, "data_files"):
            for i, df in enumerate(self.visualizer.data_files):
                filename = df["source_file"].iloc[0]
                device = df["device"].iloc[0]
                record_count = len(df)
                display_text = f"{filename} [{device}] ({record_count} records)"
                self.file_listbox.insert(tk.END, display_text)
        self.update_selection_label()

    def select_all_files(self):
        """Select all files in the listbox"""
        self.file_listbox.select_set(0, tk.END)
        self.update_selection_label()

    def clear_file_selection(self):
        """Clear all file selections"""
        self.file_listbox.selection_clear(0, tk.END)
        self.update_selection_label()

    def select_by_device(self):
        """Open dialog to select files by device name"""
        if not hasattr(self.visualizer, "data_files") or not self.visualizer.data_files:
            return

        # Get unique devices
        devices = set()
        for df in self.visualizer.data_files:
            devices.add(df["device"].iloc[0])

        device_window = tk.Toplevel(self.root)
        device_window.title("Select by Device")
        device_window.geometry("300x200")

        ttk.Label(device_window, text="Select devices:").pack(pady=10)

        device_vars = {}
        for device in sorted(devices):
            var = tk.BooleanVar()
            ttk.Checkbutton(device_window, text=device, variable=var).pack(
                anchor=tk.W, padx=20
            )
            device_vars[device] = var

        def apply_device_selection():
            selected_devices = [
                device for device, var in device_vars.items() if var.get()
            ]
            self.file_listbox.selection_clear(0, tk.END)

            for i, df in enumerate(self.visualizer.data_files):
                if df["device"].iloc[0] in selected_devices:
                    self.file_listbox.selection_set(i)

            self.update_selection_label()
            device_window.destroy()

        ttk.Button(device_window, text="Apply", command=apply_device_selection).pack(
            pady=10
        )

    def update_selection_label(self):
        """Update the selection status label"""
        selected_indices = self.file_listbox.curselection()
        if selected_indices:
            total_records = 0
            devices = set()
            for i in selected_indices:
                df = self.visualizer.data_files[i]
                total_records += len(df)
                devices.add(df["device"].iloc[0])

            self.selection_label.config(
                text=f"Selected: {len(selected_indices)} files, {total_records} records, {len(devices)} devices"
            )
        else:
            self.selection_label.config(text="No files selected")

    def get_selected_data(self):
        """Get combined data from selected files only"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one file")
            return None

        selected_dataframes = [self.visualizer.data_files[i] for i in selected_indices]
        combined = pd.concat(selected_dataframes, ignore_index=True)
        return combined.sort_values("timestamp").reset_index(drop=True)

    def create_animated_heatmap(self):
        """Create animated heatmap visualization"""
        if not self.data_loaded:
            messagebox.showwarning("Warning", "Please load data first")
            return

        selected_data = self.get_selected_data()
        if selected_data is None:
            return

        try:
            time_window = int(self.time_window_var.get())

            # Temporarily replace the visualizer's combined_data with selected data
            original_data = self.visualizer.combined_data
            self.visualizer.combined_data = selected_data
            self.visualizer.time_window = time_window
            self.visualizer.create_animated_heatmap()
            # Restore original data
            self.visualizer.combined_data = original_data
        except ValueError:
            messagebox.showerror("Error", "Invalid time window size")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create heatmap: {e}")

    def create_time_series(self):
        """Create time series plots"""
        if not self.data_loaded:
            messagebox.showwarning("Warning", "Please load data first")
            return

        selected_data = self.get_selected_data()
        if selected_data is None:
            return

        try:
            channels_str = self.channels_var.get()
            channels = [int(ch.strip()) for ch in channels_str.split(",")]

            # Temporarily replace the visualizer's combined_data with selected data
            original_data = self.visualizer.combined_data
            self.visualizer.combined_data = selected_data
            self.visualizer.create_channel_time_series(channels)
            # Restore original data
            self.visualizer.combined_data = original_data
        except ValueError:
            messagebox.showerror(
                "Error", "Invalid channel list format. Use comma-separated numbers."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create time series: {e}")

    def create_device_comparison(self):
        """Create device comparison visualization"""
        if not self.data_loaded:
            messagebox.showwarning("Warning", "Please load data first")
            return

        selected_data = self.get_selected_data()
        if selected_data is None:
            return

        try:
            # Temporarily replace the visualizer's combined_data with selected data
            original_data = self.visualizer.combined_data
            self.visualizer.combined_data = selected_data
            self.visualizer.create_device_comparison()
            # Restore original data
            self.visualizer.combined_data = original_data
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create comparison: {e}")

    def create_individual_file_view(self):
        """Create individual file view - show each selected file separately"""
        if not self.data_loaded:
            messagebox.showwarning("Warning", "Please load data first")
            return

        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one file")
            return

        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(
                len(selected_indices),
                1,
                figsize=(14, 3 * len(selected_indices)),
                sharex=True,
            )
            if len(selected_indices) == 1:
                axes = [axes]

            for i, file_idx in enumerate(selected_indices):
                df = self.visualizer.data_files[file_idx]
                filename = df["source_file"].iloc[0]
                device = df["device"].iloc[0]

                # Get channel data
                channel_cols = [col for col in df.columns if col.startswith("Ch")]
                channel_data = df[channel_cols].values

                if len(channel_data) > 0:
                    # Create colormap
                    colors = [(0, 0, 0.8), (0, 0.8, 0), (0.8, 0.8, 0), (0.8, 0, 0)]
                    cmap = LinearSegmentedColormap.from_list(
                        "spectrum_cmap", colors, N=256
                    )

                    im = axes[i].imshow(
                        channel_data.T, aspect="auto", cmap=cmap, interpolation="none"
                    )
                    axes[i].set_title(
                        f"{filename} - Device: {device} ({len(df)} records)",
                        fontweight="bold",
                        fontsize=12,
                    )
                    axes[i].set_ylabel("Channel")

                    # Y-axis ticks
                    y_ticks = np.arange(0, len(channel_cols), 20)
                    axes[i].set_yticks(y_ticks)
                    axes[i].set_yticklabels([f"{tick+1}" for tick in y_ticks])

                    # Add WiFi channel markers
                    wifi_channels = [1, 6, 11]
                    for ch in wifi_channels:
                        axes[i].axhline(
                            y=ch - 1,
                            color="white",
                            linestyle="--",
                            alpha=0.7,
                            linewidth=1,
                        )

            if axes:
                axes[-1].set_xlabel("Time Points")

            plt.suptitle("Individual File Views", fontsize=16, fontweight="bold")
            plt.tight_layout()
            plt.show()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create individual file view: {e}")

    def create_file_summary(self):
        """Create summary statistics for selected files"""
        if not self.data_loaded:
            messagebox.showwarning("Warning", "Please load data first")
            return

        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one file")
            return

        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(2, 2, figsize=(16, 10))

            # Collect data for analysis
            file_stats = []
            channel_cols = None

            for file_idx in selected_indices:
                df = self.visualizer.data_files[file_idx]
                filename = df["source_file"].iloc[0]
                device = df["device"].iloc[0]

                if channel_cols is None:
                    channel_cols = [col for col in df.columns if col.startswith("Ch")]

                channel_data = df[channel_cols].values

                stats = {
                    "filename": filename,
                    "device": device,
                    "records": len(df),
                    "duration": (df["timestamp"].max() - df["timestamp"].min()) / 1000,
                    "total_activity": np.sum(channel_data),
                    "avg_activity": np.mean(channel_data),
                    "max_activity": np.max(channel_data),
                    "channel_avg": np.mean(channel_data, axis=0),
                }
                file_stats.append(stats)

            # Plot 1: Total activity comparison
            ax = axes[0, 0]
            filenames = [
                (
                    stat["filename"][:20] + "..."
                    if len(stat["filename"]) > 20
                    else stat["filename"]
                )
                for stat in file_stats
            ]
            total_activities = [stat["total_activity"] for stat in file_stats]
            bars = ax.bar(range(len(file_stats)), total_activities, alpha=0.7)
            ax.set_title("Total Activity by File")
            ax.set_ylabel("Total Activity")
            ax.set_xticks(range(len(file_stats)))
            ax.set_xticklabels(filenames, rotation=45, ha="right")

            # Add value labels
            for bar, value in zip(bars, total_activities):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{value:.0f}",
                    ha="center",
                    va="bottom",
                )

            # Plot 2: Duration comparison
            ax = axes[0, 1]
            durations = [stat["duration"] for stat in file_stats]
            bars = ax.bar(range(len(file_stats)), durations, alpha=0.7, color="orange")
            ax.set_title("Recording Duration by File")
            ax.set_ylabel("Duration (seconds)")
            ax.set_xticks(range(len(file_stats)))
            ax.set_xticklabels(filenames, rotation=45, ha="right")

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

            # Plot 3: Average channel activity
            ax = axes[1, 0]
            for i, stat in enumerate(file_stats):
                ax.plot(
                    range(1, len(stat["channel_avg"]) + 1),
                    stat["channel_avg"],
                    label=f"{stat['device']}",
                    alpha=0.8,
                    linewidth=2,
                )
            ax.set_title("Average Activity by Channel")
            ax.set_xlabel("Channel Number")
            ax.set_ylabel("Average Activity")
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Plot 4: File statistics table
            ax = axes[1, 1]
            ax.axis("tight")
            ax.axis("off")

            table_data = []
            headers = [
                "Device",
                "Records",
                "Duration (s)",
                "Avg Activity",
                "Max Activity",
            ]

            for stat in file_stats:
                row = [
                    stat["device"],
                    f"{stat['records']}",
                    f"{stat['duration']:.1f}",
                    f"{stat['avg_activity']:.2f}",
                    f"{stat['max_activity']:.0f}",
                ]
                table_data.append(row)

            table = ax.table(
                cellText=table_data, colLabels=headers, cellLoc="center", loc="center"
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.5)
            ax.set_title("File Statistics Summary", pad=20)

            plt.suptitle("Selected Files Summary", fontsize=16, fontweight="bold")
            plt.tight_layout()
            plt.show()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create file summary: {e}")


def main():
    """Main function to run the GUI application"""
    root = tk.Tk()
    app = RFVisualizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    # Can be used both as GUI and standalone
    import sys

    if len(sys.argv) > 1:
        # Command line usage
        data_dir = sys.argv[1]
        visualizer = RFTimeSeriesVisualizer()
        visualizer.load_data_files(data_dir)

        if len(sys.argv) > 2 and sys.argv[2] == "heatmap":
            visualizer.create_animated_heatmap()
        elif len(sys.argv) > 2 and sys.argv[2] == "timeseries":
            visualizer.create_channel_time_series()
        else:
            visualizer.create_animated_heatmap()
    else:
        # GUI mode
        main()
