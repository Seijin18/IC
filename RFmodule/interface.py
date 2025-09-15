# --- Tkinter version ---
import sys
import os
from datetime import datetime
import threading
import time
import pandas as pd
import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.widgets import Slider
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import numpy as np
import glob


class SerialReaderThread(threading.Thread):
    def __init__(self, port, baudrate=115200, callback=None):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self._running = threading.Event()
        self._running.set()
        self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            while self._running.is_set():
                line = self.ser.readline().decode("utf-8").strip()
                if line:
                    parts = line.split(",")
                    if len(parts) > 1:
                        try:
                            values = [int(parts[0])] + [int(x) for x in parts[1:]]
                            if self.callback:
                                self.callback(values)
                        except Exception:
                            continue
        except Exception as e:
            pass
        finally:
            if self.ser:
                self.ser.close()

    def stop(self):
        self._running.clear()


class LivePlotCanvas:
    def __init__(self, parent, n_channels=126):
        self.n_channels = n_channels
        self.data = []
        self.fig = Figure(figsize=(8, 4))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Channel")
        self.ax.set_ylabel("Value")
        self.ax.set_xlim(0, n_channels - 1)
        self.ax.set_ylim(0, 100)
        self.ax.grid(True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

    def update_plot(self, values):
        self.data.append(values)
        y = values[1:]
        x = list(range(len(y)))
        self.ax.clear()
        self.ax.set_xlabel("Channel")
        self.ax.set_ylabel("Value")
        self.ax.set_xlim(0, self.n_channels - 1)
        self.ax.set_ylim(0, 100)
        self.ax.grid(True)
        self.ax.plot(x, y, color="b")
        self.canvas.draw()

    def get_dataframe(self):
        if not self.data:
            return pd.DataFrame()
        columns = ["timestamp"] + [f"Ch{i}" for i in range(1, len(self.data[0]))]
        return pd.DataFrame(self.data, columns=columns)


class MainWindow:

    def __init__(self, root):
        self.root = root
        self.root.title("Serial Spectrum Reader (Tkinter)")
        self.root.geometry("950x600")

        top_frame = tk.Frame(root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        tk.Label(top_frame, text="Serial Port:").pack(side=tk.LEFT)
        self.combobox = ttk.Combobox(top_frame, state="readonly", width=20)
        self.combobox.pack(side=tk.LEFT, padx=5)
        self.refresh_ports()

        self.start_btn = tk.Button(top_frame, text="Start", command=self.start_reading)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(
            top_frame, text="Stop", command=self.stop_reading, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Elapsed time label
        self.time_label = tk.Label(top_frame, text="Elapsed Time: 00:00:00")
        self.time_label.pack(side=tk.LEFT, padx=15)

        # Add visualization button
        self.visualize_btn = tk.Button(
            top_frame, text="Open Time Series Visualizer", command=self.open_visualizer
        )
        self.visualize_btn.pack(side=tk.LEFT, padx=5)

        self._start_time = None
        self._timer_running = False

        # Plot
        self.plot = LivePlotCanvas(root)

        self.reader_thread = None
        self._lock = threading.Lock()

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.combobox["values"] = port_list
        if port_list:
            self.combobox.current(0)

    def start_reading(self):
        port = self.combobox.get()
        if not port:
            messagebox.showwarning("Error", "No serial port selected.")
            return
        self.plot.data = []
        self.reader_thread = SerialReaderThread(port, callback=self.on_data_received)
        self.reader_thread.daemon = True
        self.reader_thread.start()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.combobox.config(state=tk.DISABLED)
        # Start timer
        self._start_time = time.time()
        self._timer_running = True
        self.update_elapsed_time()

    def on_data_received(self, values):
        # Called from thread, so use after_idle to update plot in main thread
        self.root.after(0, lambda: self.plot.update_plot(values))

    def stop_reading(self):

        if self.reader_thread:
            self.reader_thread.stop()
            self.reader_thread.join()
        self._timer_running = False
        df = self.plot.get_dataframe()
        if not df.empty:
            # Save to 'saved_data' folder in project directory
            save_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "saved_data"
            )
            os.makedirs(save_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = os.path.join(save_dir, f"spectrum_data_{timestamp}.csv")
            df.to_csv(fname, index=False)
            messagebox.showinfo("Data Saved", f"Data saved to {fname}")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.combobox.config(state=tk.NORMAL)
        self.time_label.config(text="Elapsed Time: 00:00:00")

    def update_elapsed_time(self):
        if self._timer_running and self._start_time is not None:
            elapsed = int(time.time() - self._start_time)
            h = elapsed // 3600
            m = (elapsed % 3600) // 60
            s = elapsed % 60
            self.time_label.config(text=f"Elapsed Time: {h:02d}:{m:02d}:{s:02d}")
            self.root.after(1000, self.update_elapsed_time)

    def open_visualizer(self):
        """Open the time series visualizer window"""
        TimeSeriesVisualizerWindow(self.root)


class TimeSeriesVisualizerWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("RF Time Series Visualizer")
        self.window.geometry("1000x800")

        self.data_files = []
        self.combined_data = None
        self.current_plot_type = None

        self.setup_gui()

    def setup_gui(self):
        """Setup the visualizer GUI"""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Load data button
        ttk.Button(control_frame, text="Load Saved Data", command=self.load_data).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        # Status label
        self.status_label = ttk.Label(control_frame, text="No data loaded")
        self.status_label.pack(side=tk.LEFT, padx=(0, 20))

        # File selection frame
        file_select_frame = ttk.LabelFrame(
            main_frame, text="File Selection", padding="10"
        )
        file_select_frame.pack(fill=tk.X, pady=(0, 10))

        # File listbox with scrollbar
        list_container = ttk.Frame(file_select_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        self.file_listbox = tk.Listbox(list_container, selectmode=tk.MULTIPLE, height=4)
        file_scrollbar = ttk.Scrollbar(
            list_container, orient="vertical", command=self.file_listbox.yview
        )
        self.file_listbox.configure(yscrollcommand=file_scrollbar.set)

        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # File selection buttons
        file_btn_frame = ttk.Frame(file_select_frame)
        file_btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(
            file_btn_frame, text="Select All", command=self.select_all_files
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_btn_frame, text="Clear", command=self.clear_selection).pack(
            side=tk.LEFT, padx=5
        )

        # Selection status
        self.selection_label = ttk.Label(file_btn_frame, text="No files selected")
        self.selection_label.pack(side=tk.RIGHT)

        # Visualization buttons
        ttk.Button(
            control_frame, text="Heatmap with Slider", command=self.show_heatmap_slider
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Channel Time Series",
            command=self.show_channel_timeseries,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame, text="Device Comparison", command=self.show_device_comparison
        ).pack(side=tk.LEFT, padx=5)

        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # Time window setting
        ttk.Label(config_frame, text="Time Window:").pack(side=tk.LEFT)
        self.time_window_var = tk.StringVar(value="100")
        ttk.Entry(config_frame, textvariable=self.time_window_var, width=8).pack(
            side=tk.LEFT, padx=(5, 15)
        )

        # Channels setting
        ttk.Label(config_frame, text="Channels (comma-separated):").pack(side=tk.LEFT)
        self.channels_var = tk.StringVar(value="1,6,11,40,80")
        ttk.Entry(config_frame, textvariable=self.channels_var, width=15).pack(
            side=tk.LEFT, padx=5
        )

        # Plot frame
        self.plot_frame = ttk.Frame(main_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)

        self.current_canvas = None

    def load_data(self):
        """Load data from saved_data directory"""
        # Default to saved_data directory
        default_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "saved_data"
        )
        directory = filedialog.askdirectory(
            title="Select Data Directory",
            initialdir=default_dir if os.path.exists(default_dir) else None,
        )

        if directory:
            try:
                self.load_data_files(directory)
                if self.combined_data is not None:
                    num_records = len(self.combined_data)
                    num_files = len(self.data_files)
                    devices = self.combined_data["device"].unique()
                    self.status_label.config(
                        text=f"Loaded {num_records} records from {num_files} files ({len(devices)} devices)"
                    )
                    self.populate_file_list()
                else:
                    self.status_label.config(text="No valid data files found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load data: {e}")

    def load_data_files(self, directory_path):
        """Load all CSV files from the directory"""
        csv_files = glob.glob(os.path.join(directory_path, "*.csv"))
        self.data_files = []

        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)
                filename = os.path.basename(file_path)
                df["source_file"] = filename

                # Extract device name from filename
                if "(" in filename and ")" in filename:
                    device_name = filename.split("(")[1].split(")")[0]
                    df["device"] = device_name
                else:
                    df["device"] = filename.replace(".csv", "").replace(
                        "spectrum_data_", ""
                    )

                self.data_files.append(df)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

        if self.data_files:
            self.combined_data = pd.concat(self.data_files, ignore_index=True)
            self.combined_data = self.combined_data.sort_values(
                "timestamp"
            ).reset_index(drop=True)

    def populate_file_list(self):
        """Populate the file selection listbox"""
        self.file_listbox.delete(0, tk.END)
        for i, df in enumerate(self.data_files):
            filename = df["source_file"].iloc[0]
            device = df["device"].iloc[0]
            record_count = len(df)
            display_text = f"{filename} [{device}] ({record_count} records)"
            self.file_listbox.insert(tk.END, display_text)
        # Select all by default
        self.file_listbox.select_set(0, tk.END)
        self.update_selection_label()

    def select_all_files(self):
        """Select all files"""
        self.file_listbox.select_set(0, tk.END)
        self.update_selection_label()

    def clear_selection(self):
        """Clear file selection"""
        self.file_listbox.selection_clear(0, tk.END)
        self.update_selection_label()

    def update_selection_label(self):
        """Update selection status label"""
        selected_indices = self.file_listbox.curselection()
        if selected_indices:
            total_records = sum(len(self.data_files[i]) for i in selected_indices)
            devices = set(
                self.data_files[i]["device"].iloc[0] for i in selected_indices
            )
            self.selection_label.config(
                text=f"Selected: {len(selected_indices)} files, {total_records} records, {len(devices)} devices"
            )
        else:
            self.selection_label.config(text="No files selected")

    def get_selected_data(self):
        """Get data from selected files only"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one file")
            return None

        selected_dataframes = [self.data_files[i] for i in selected_indices]
        combined = pd.concat(selected_dataframes, ignore_index=True)
        return combined.sort_values("timestamp").reset_index(drop=True)

    def clear_plot(self):
        """Clear the current plot"""
        if self.current_canvas:
            self.current_canvas.get_tk_widget().destroy()
            self.current_canvas = None

    def show_heatmap_slider(self):
        """Show heatmap with time slider"""
        selected_data = self.get_selected_data()
        if selected_data is None:
            return

        self.clear_plot()

        try:
            time_window = int(self.time_window_var.get())

            # Get channel data
            channel_cols = [
                col for col in selected_data.columns if col.startswith("Ch")
            ]
            channel_data = selected_data[channel_cols].values
            timestamps = selected_data["timestamp"].values

            # Get info about selected files
            selected_indices = self.file_listbox.curselection()
            selected_files = [
                self.data_files[i]["source_file"].iloc[0] for i in selected_indices
            ]
            selected_devices = list(
                set([self.data_files[i]["device"].iloc[0] for i in selected_indices])
            )

            # Create figure with slider
            fig = plt.Figure(figsize=(12, 8))
            gs = fig.add_gridspec(2, 1, height_ratios=[10, 1], hspace=0.3)

            ax_main = fig.add_subplot(gs[0])
            ax_slider = fig.add_subplot(gs[1])

            # Create colormap
            colors = [(0, 0, 0.8), (0, 0.8, 0), (0.8, 0.8, 0), (0.8, 0, 0)]
            cmap = LinearSegmentedColormap.from_list("spectrum_cmap", colors, N=256)

            # Initial plot
            initial_data = channel_data[:time_window].T
            im = ax_main.imshow(
                initial_data, aspect="auto", cmap=cmap, interpolation="none"
            )

            # Create title with file information
            devices_str = (
                ", ".join(selected_devices)
                if len(selected_devices) <= 3
                else f"{len(selected_devices)} devices"
            )
            title = (
                f"RF Spectrum Activity - {devices_str} ({len(selected_data)} records)"
            )
            ax_main.set_title(title, fontsize=12, fontweight="bold")
            ax_main.set_xlabel("Time Points")
            ax_main.set_ylabel("Channel (2400 + ch MHz)")

            # Y-axis setup
            y_ticks = np.arange(0, len(channel_cols), 10)
            ax_main.set_yticks(y_ticks)
            ax_main.set_yticklabels([f"{tick+1}" for tick in y_ticks])

            # Add WiFi channel markers
            wifi_channels = [1, 6, 11]
            for ch in wifi_channels:
                ax_main.axhline(
                    y=ch - 1, color="white", linestyle="--", alpha=0.7, linewidth=1
                )

            # Colorbar
            cbar = fig.colorbar(im, ax=ax_main)
            cbar.set_label("Activity Level")

            # Add text box with file information
            file_info = f"Files: {len(selected_files)}, Devices: {devices_str}"
            ax_main.text(
                0.02,
                0.98,
                file_info,
                transform=ax_main.transAxes,
                bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8),
                verticalalignment="top",
                fontsize=9,
            )

            # Slider setup (simplified for tkinter)
            ax_slider.set_xlim(0, max(1, len(channel_data) - time_window))
            ax_slider.set_ylim(-1, 1)
            ax_slider.set_xlabel("Time Position")
            ax_slider.set_yticks([])

            self.current_canvas = FigureCanvasTkAgg(fig, self.plot_frame)
            self.current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create heatmap: {e}")

    def show_channel_timeseries(self):
        """Show time series for selected channels"""
        selected_data = self.get_selected_data()
        if selected_data is None:
            return

        self.clear_plot()

        try:
            channels_str = self.channels_var.get()
            channels = [int(ch.strip()) for ch in channels_str.split(",")]

            # Get info about selected files
            selected_indices = self.file_listbox.curselection()
            selected_devices = list(
                set([self.data_files[i]["device"].iloc[0] for i in selected_indices])
            )

            fig = plt.Figure(figsize=(12, 8))

            timestamps = selected_data["timestamp"].values / 1000  # Convert to seconds

            # Create subplots for each channel
            n_channels = len(channels)
            axes = []

            for i, ch in enumerate(channels):
                if i == 0:
                    ax = fig.add_subplot(n_channels, 1, i + 1)
                else:
                    ax = fig.add_subplot(n_channels, 1, i + 1, sharex=axes[0])
                axes.append(ax)

                col_name = f"Ch{ch}"
                if col_name in selected_data.columns:
                    data = selected_data[col_name].values
                    ax.plot(timestamps, data, linewidth=1, alpha=0.8, color=f"C{i}")
                    ax.set_ylabel(f"Ch{ch}\n({2400+ch} MHz)", rotation=0, labelpad=50)
                    ax.grid(True, alpha=0.3)
                    ax.set_ylim(0, max(data) * 1.1 if max(data) > 0 else 1)

            if axes:
                axes[-1].set_xlabel("Time (seconds)")

            # Create title with file information
            devices_str = (
                ", ".join(selected_devices)
                if len(selected_devices) <= 3
                else f"{len(selected_devices)} devices"
            )
            title = (
                f"RF Channel Activity - {devices_str} ({len(selected_data)} records)"
            )
            fig.suptitle(title, fontsize=12, fontweight="bold")

            self.current_canvas = FigureCanvasTkAgg(fig, self.plot_frame)
            self.current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create time series: {e}")

    def show_device_comparison(self):
        """Show comparison between different devices"""
        selected_data = self.get_selected_data()
        if selected_data is None:
            return

        devices = selected_data["device"].unique()
        if len(devices) <= 1:
            messagebox.showinfo(
                "Info", "Need data from multiple devices for comparison"
            )
            return

        self.clear_plot()

        try:
            fig = plt.Figure(figsize=(12, 10))

            channel_cols = [
                col for col in selected_data.columns if col.startswith("Ch")
            ]

            for i, device in enumerate(devices):
                ax = fig.add_subplot(len(devices), 1, i + 1)

                device_data = selected_data[selected_data["device"] == device]
                channel_data = device_data[channel_cols].values

                if len(channel_data) > 0:
                    im = ax.imshow(
                        channel_data.T, aspect="auto", cmap="hot", interpolation="none"
                    )
                    ax.set_title(
                        f"Device: {device} ({len(device_data)} records)",
                        fontweight="bold",
                    )
                    ax.set_ylabel("Channel")

                    if i == len(devices) - 1:
                        ax.set_xlabel("Time Points")

            # Get info about selected files
            selected_indices = self.file_listbox.curselection()
            num_files = len(selected_indices)
            title = f"RF Spectrum Comparison - {len(devices)} Devices from {num_files} Files"
            fig.suptitle(title, fontsize=12, fontweight="bold")

            self.current_canvas = FigureCanvasTkAgg(fig, self.plot_frame)
            self.current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create comparison: {e}")


def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
