"""
RF Spectrum Analyzer - Main Interface
Reads 2.4 GHz spectrum data from an NRF24L01-equipped ESP32/Arduino and
provides live visualization and stored-data review.

Usage:
    python main.py
"""

import os
import re
import glob
import threading
import time
from datetime import datetime

import numpy as np
import pandas as pd
import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SAVED_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_data")
N_CHANNELS = 126
BAUD_RATE = 115200
WIFI_CHANNELS = {1: 12, 6: 37, 11: 62}   # WiFi ch -> NRF channel index (approx)

# Custom heatmap colormap
_HEATMAP_COLORS = [(0, 0, 0.8), (0, 0.8, 0), (0.8, 0.8, 0), (0.8, 0, 0)]
SPECTRUM_CMAP = LinearSegmentedColormap.from_list("spectrum", _HEATMAP_COLORS, N=256)


# ---------------------------------------------------------------------------
# Serial reader thread
# ---------------------------------------------------------------------------
class SerialReaderThread(threading.Thread):
    """Background thread that reads comma-separated lines from a serial port.

    Each line is expected to be:
        <timestamp_ms>,<ch0>,<ch1>,...,<ch125>

    On each valid sample the *callback* is called with a list of ints.
    """

    def __init__(self, port: str, baudrate: int = BAUD_RATE, callback=None):
        super().__init__(daemon=True)
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self._stop_event = threading.Event()

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(1)  # let the board reset
            ser.flushInput()
            while not self._stop_event.is_set():
                raw = ser.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) < 2:
                    continue
                try:
                    values = [int(p) for p in parts]
                    if self.callback:
                        self.callback(values)
                except ValueError:
                    continue
            ser.close()
        except Exception:
            pass

    def stop(self):
        self._stop_event.set()


# ---------------------------------------------------------------------------
# Live spectrum canvas
# ---------------------------------------------------------------------------
class LiveSpectrumCanvas:
    """Matplotlib canvas embedded in a Tk parent that shows a live line plot."""

    def __init__(self, parent):
        self.fig = Figure(figsize=(9, 4), tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self._setup_axes()
        (self.line,) = self.ax.plot(
            range(N_CHANNELS), [0] * N_CHANNELS, color="#2196F3", linewidth=1.2
        )
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _setup_axes(self):
        self.ax.set_xlim(0, N_CHANNELS - 1)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlabel("Channel  (2400 + ch MHz)")
        self.ax.set_ylabel("Activity (%)")
        self.ax.set_title("Live RF Spectrum")
        self.ax.grid(True, alpha=0.3)
        # Mark Wi-Fi channels
        for label, ch in WIFI_CHANNELS.items():
            self.ax.axvline(ch, color="orange", linestyle="--", alpha=0.6, linewidth=1)
            self.ax.text(
                ch + 0.5, 95, f"Wi-Fi {label}", color="orange", fontsize=7, va="top"
            )

    def update(self, channel_values: list):
        y = channel_values[:N_CHANNELS]
        x = list(range(len(y)))
        self.line.set_xdata(x)
        self.line.set_ydata(y)
        self.canvas.draw_idle()


# ---------------------------------------------------------------------------
# Record tab
# ---------------------------------------------------------------------------
class RecordTab(ttk.Frame):
    """Tab for live serial recording."""

    def __init__(self, parent):
        super().__init__(parent)
        self._samples: list = []
        self._reader: SerialReaderThread | None = None
        self._start_time: float | None = None
        self._timer_running = False

        self._build_controls()
        self._build_plot()

    # --- GUI construction ---------------------------------------------------

    def _build_controls(self):
        ctrl = ttk.LabelFrame(self, text="Serial Connection", padding=8)
        ctrl.pack(fill=tk.X, padx=10, pady=(10, 4))

        # Port row
        port_row = ttk.Frame(ctrl)
        port_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(port_row, text="Port:").pack(side=tk.LEFT)
        self._port_cb = ttk.Combobox(port_row, state="readonly", width=18)
        self._port_cb.pack(side=tk.LEFT, padx=(4, 8))
        ttk.Button(port_row, text="Refresh", command=self._refresh_ports).pack(
            side=tk.LEFT
        )

        # Filename row
        fname_row = ttk.Frame(ctrl)
        fname_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(fname_row, text="Save as:").pack(side=tk.LEFT)
        self._fname_var = tk.StringVar(value="my_recording")
        self._fname_entry = ttk.Entry(fname_row, textvariable=self._fname_var, width=30)
        self._fname_entry.pack(side=tk.LEFT, padx=(4, 4))
        ttk.Label(fname_row, text=".csv  →  saved_data/", foreground="gray").pack(
            side=tk.LEFT
        )

        # Action row
        action_row = ttk.Frame(ctrl)
        action_row.pack(fill=tk.X)
        self._start_btn = ttk.Button(
            action_row, text="▶  Start", command=self._start
        )
        self._start_btn.pack(side=tk.LEFT, padx=(0, 6))
        self._stop_btn = ttk.Button(
            action_row, text="■  Stop & Save", command=self._stop, state=tk.DISABLED
        )
        self._stop_btn.pack(side=tk.LEFT, padx=(0, 20))
        self._time_lbl = ttk.Label(action_row, text="Elapsed: 00:00:00")
        self._time_lbl.pack(side=tk.LEFT)
        self._sample_lbl = ttk.Label(action_row, text="  Samples: 0", foreground="gray")
        self._sample_lbl.pack(side=tk.LEFT)

        self._refresh_ports()

    def _build_plot(self):
        plot_frame = ttk.LabelFrame(self, text="Live Signal", padding=4)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 10))
        self._live_canvas = LiveSpectrumCanvas(plot_frame)

    # --- Port utilities -----------------------------------------------------

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self._port_cb["values"] = ports
        if ports:
            self._port_cb.current(0)

    # --- Recording controls -------------------------------------------------

    def _start(self):
        port = self._port_cb.get()
        if not port:
            messagebox.showwarning("No Port", "Please select a serial port.")
            return
        fname = self._fname_var.get().strip()
        if not fname:
            messagebox.showwarning("No Filename", "Please enter a filename.")
            return
        # Sanitise filename
        fname = re.sub(r'[<>:"/\\|?*]', "_", fname)
        self._fname_var.set(fname)

        self._samples = []
        self._start_time = time.time()
        self._timer_running = True
        self._reader = SerialReaderThread(port, callback=self._on_sample)
        self._reader.start()

        self._start_btn.config(state=tk.DISABLED)
        self._stop_btn.config(state=tk.NORMAL)
        self._port_cb.config(state=tk.DISABLED)
        self._fname_entry.config(state=tk.DISABLED)
        self._tick_timer()

    def _stop(self):
        self._timer_running = False
        if self._reader:
            self._reader.stop()
            self._reader.join(timeout=3)
            self._reader = None

        self._start_btn.config(state=tk.NORMAL)
        self._stop_btn.config(state=tk.DISABLED)
        self._port_cb.config(state=tk.NORMAL)
        self._fname_entry.config(state=tk.NORMAL)
        self._time_lbl.config(text="Elapsed: 00:00:00")

        self._save_data()

    def _on_sample(self, values: list):
        self._samples.append(values)
        # Update GUI from main thread
        self.after(0, lambda v=values: self._gui_update(v))

    def _gui_update(self, values: list):
        self._live_canvas.update(values[1:])  # skip timestamp
        self._sample_lbl.config(text=f"  Samples: {len(self._samples)}")

    def _tick_timer(self):
        if not self._timer_running:
            return
        elapsed = int(time.time() - self._start_time)
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        self._time_lbl.config(text=f"Elapsed: {h:02d}:{m:02d}:{s:02d}")
        self.after(1000, self._tick_timer)

    # --- Data persistence ---------------------------------------------------

    def _save_data(self):
        if not self._samples:
            messagebox.showinfo("No Data", "No samples were collected.")
            return
        os.makedirs(SAVED_DATA_DIR, exist_ok=True)
        fname = self._fname_var.get().strip() or "recording"
        path = os.path.join(SAVED_DATA_DIR, f"{fname}.csv")
        # Avoid overwriting
        if os.path.exists(path):
            base, ext = os.path.splitext(path)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"{base}_{stamp}{ext}"

        n_ch = len(self._samples[0]) - 1  # subtract timestamp column
        columns = ["timestamp"] + [f"Ch{i+1}" for i in range(n_ch)]
        df = pd.DataFrame(self._samples, columns=columns[: len(self._samples[0])])
        df.to_csv(path, index=False)
        messagebox.showinfo("Saved", f"Data saved to:\n{path}")


# ---------------------------------------------------------------------------
# View tab
# ---------------------------------------------------------------------------
class ViewTab(ttk.Frame):
    """Tab for loading and visualising stored CSV data."""

    def __init__(self, parent):
        super().__init__(parent)
        self._current_fig: Figure | None = None
        self._current_canvas: FigureCanvasTkAgg | None = None
        self._current_toolbar = None
        self._loaded_df: pd.DataFrame | None = None
        self._loaded_path: str = ""

        self._build_controls()
        self._build_plot_area()
        self._refresh_file_list()

    # --- GUI construction ---------------------------------------------------

    def _build_controls(self):
        ctrl = ttk.LabelFrame(self, text="Stored Data", padding=8)
        ctrl.pack(fill=tk.X, padx=10, pady=(10, 4))

        # File selection row
        file_row = ttk.Frame(ctrl)
        file_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(file_row, text="File:").pack(side=tk.LEFT)
        self._file_cb = ttk.Combobox(file_row, state="readonly", width=50)
        self._file_cb.pack(side=tk.LEFT, padx=(4, 8))
        ttk.Button(file_row, text="Refresh", command=self._refresh_file_list).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(file_row, text="Browse…", command=self._browse_file).pack(
            side=tk.LEFT
        )

        # Action row
        action_row = ttk.Frame(ctrl)
        action_row.pack(fill=tk.X)
        ttk.Button(action_row, text="Open & Plot", command=self._load_and_plot).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self._save_img_btn = ttk.Button(
            action_row, text="Save Image…", command=self._save_image, state=tk.DISABLED
        )
        self._save_img_btn.pack(side=tk.LEFT, padx=(0, 20))
        self._info_lbl = ttk.Label(action_row, text="", foreground="gray")
        self._info_lbl.pack(side=tk.LEFT)

    def _build_plot_area(self):
        self._plot_frame = ttk.LabelFrame(self, text="Spectrum Heatmap", padding=4)
        self._plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 10))

    # --- File list utilities ------------------------------------------------

    def _refresh_file_list(self):
        os.makedirs(SAVED_DATA_DIR, exist_ok=True)
        files = sorted(glob.glob(os.path.join(SAVED_DATA_DIR, "*.csv")))
        display = [os.path.basename(f) for f in files]
        self._file_cb["values"] = display
        self._file_cb._full_paths = files  # attach full paths
        if display:
            self._file_cb.current(len(display) - 1)

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select spectrum CSV",
            initialdir=SAVED_DATA_DIR,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self._load_file(path)

    # --- Data loading -------------------------------------------------------

    def _load_and_plot(self):
        idx = self._file_cb.current()
        paths = getattr(self._file_cb, "_full_paths", [])
        if idx < 0 or idx >= len(paths):
            messagebox.showwarning("No File", "Please select a file from the list.")
            return
        self._load_file(paths[idx])

    def _load_file(self, path: str):
        try:
            df = pd.read_csv(path)
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not read file:\n{e}")
            return

        self._loaded_df = df
        self._loaded_path = path
        n_rec = len(df)
        n_ch = len([c for c in df.columns if c.lower().startswith("ch")])
        fname = os.path.basename(path)
        self._info_lbl.config(text=f"{fname}  |  {n_rec} records  |  {n_ch} channels")
        self._plot_heatmap(df, title=fname)
        self._save_img_btn.config(state=tk.NORMAL)

    # --- Plotting -----------------------------------------------------------

    def _clear_plot(self):
        if self._current_toolbar:
            self._current_toolbar.destroy()
        if self._current_canvas:
            self._current_canvas.get_tk_widget().destroy()
        self._current_canvas = None
        self._current_toolbar = None
        self._current_fig = None

    def _plot_heatmap(self, df: pd.DataFrame, title: str = ""):
        self._clear_plot()

        # Identify channel columns (start with "Ch" or "ch")
        ch_cols = [c for c in df.columns if re.match(r"(?i)^ch\d+$", c)]
        if not ch_cols:
            messagebox.showerror(
                "Format Error",
                "No channel columns found (expected columns named Ch1, Ch2, …).",
            )
            return

        channel_data = df[ch_cols].values  # shape: (time, channels)
        ts_col = next(
            (c for c in df.columns if c.lower() == "timestamp"), df.columns[0]
        )
        timestamps = df[ts_col].values

        # Build time labels
        if timestamps[-1] > 1e5:  # assume milliseconds
            t_sec = timestamps / 1000.0
        else:
            t_sec = timestamps.astype(float)
        t_sec = t_sec - t_sec[0]  # relative seconds

        fig = Figure(figsize=(10, 5), tight_layout=True)
        ax = fig.add_subplot(111)

        im = ax.imshow(
            channel_data.T,
            aspect="auto",
            cmap=SPECTRUM_CMAP,
            interpolation="none",
            vmin=0,
            vmax=100,
            origin="lower",
        )

        # Axis labels
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Time (s)", fontsize=11)
        ax.set_ylabel("Channel  (2400 + ch MHz)", fontsize=11)

        # X ticks in seconds
        n_ticks = min(8, len(t_sec))
        idx = np.linspace(0, len(t_sec) - 1, n_ticks, dtype=int)
        ax.set_xticks(idx)
        ax.set_xticklabels([f"{t_sec[i]:.1f}" for i in idx], rotation=30, ha="right")

        # Y ticks
        y_step = max(1, len(ch_cols) // 10)
        y_ticks = list(range(0, len(ch_cols), y_step))
        ax.set_yticks(y_ticks)
        ax.set_yticklabels([f"{t+1} ({2400+t+1} MHz)" for t in y_ticks], fontsize=8)

        # Wi-Fi markers
        for wlabel, wch in WIFI_CHANNELS.items():
            if wch < len(ch_cols):
                ax.axhline(wch, color="white", linestyle="--", alpha=0.5, linewidth=1)
                ax.text(
                    0.5,
                    wch + 0.5,
                    f"Wi-Fi {wlabel}",
                    color="white",
                    fontsize=7,
                    va="bottom",
                )

        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
        cbar.set_label("Activity (%)", fontsize=10)

        self._current_fig = fig
        self._current_canvas = FigureCanvasTkAgg(fig, self._plot_frame)
        self._current_toolbar = NavigationToolbar2Tk(
            self._current_canvas, self._plot_frame
        )
        self._current_toolbar.update()
        self._current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._current_canvas.draw()

    # --- Image export -------------------------------------------------------

    def _save_image(self):
        if self._current_fig is None:
            return
        default_name = os.path.splitext(os.path.basename(self._loaded_path))[0] + ".png"
        path = filedialog.asksaveasfilename(
            title="Save image",
            initialdir=SAVED_DATA_DIR,
            initialfile=default_name,
            defaultextension=".png",
            filetypes=[
                ("PNG image", "*.png"),
                ("JPEG image", "*.jpg"),
                ("PDF document", "*.pdf"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._current_fig.savefig(path, dpi=150, bbox_inches="tight")
            messagebox.showinfo("Saved", f"Image saved to:\n{path}")


# ---------------------------------------------------------------------------
# Application shell
# ---------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RF Spectrum Analyzer")
        self.geometry("1000x680")
        self.resizable(True, True)

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._record_tab = RecordTab(notebook)
        self._view_tab = ViewTab(notebook)

        notebook.add(self._record_tab, text="  Record  ")
        notebook.add(self._view_tab, text="  View Stored Data  ")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        # Stop any active reader before closing
        reader = getattr(self._record_tab, "_reader", None)
        if reader:
            reader.stop()
        self.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()
