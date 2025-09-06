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


def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
