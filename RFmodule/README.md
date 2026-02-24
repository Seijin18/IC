# RF Spectrum Analyzer

A Python GUI tool for recording and visualising 2.4 GHz RF spectrum data gathered by an ESP32 with an NRF24L01 module.

---

## Hardware

### Wiring (NRF24L01  ESP32)

| NRF24L01 pin | ESP32 pin |
|---|---|
| VCC | 3.3 V |
| GND | GND |
| CE | GPIO 2 |
| CSN | GPIO 4 |
| SCK | GPIO 18 |
| MOSI | GPIO 23 |
| MISO | GPIO 19 |

### Firmware

Upload `moduleTest/moduleTest.ino` to the ESP32 (115 200 baud).
The sketch sends comma-separated lines on the serial port:

```
<timestamp_ms>,<ch1>,<ch2>,...,<ch126>
```

---

## Installation

### 1  Python

Python 3.10 or later is required. Download from https://www.python.org/downloads/.

### 2  Virtual environment (recommended)

```powershell
cd RFmodule
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
# source .venv/bin/activate     # Linux / macOS
```

### 3  Dependencies

```powershell
pip install -r requirements.txt
```

---

## Running

```powershell
python main.py
```

The window opens with two tabs.

---

## Record tab

Use this tab to capture live data from the board.

1. **Port**  select the COM port of the connected ESP32 and click **Refresh** if it is not listed.
2. **Save as**  type a name for the recording (e.g. `wifi_test`). The file will be saved as `saved_data/<name>.csv`. If the name is already taken, a timestamp is appended automatically.
3. Click ** Start** to begin reading. The live spectrum plot updates in real time and the elapsed time and sample count are shown.
4. Click ** Stop & Save** to stop the recording and write the CSV file.

---

## View Stored Data tab

Use this tab to inspect previously collected CSV files.

1. The **File** dropdown is pre-populated with every CSV in the `saved_data/` folder. Click **Refresh** after adding new files, or click **Browse** to open any CSV on disk.
2. Click **Open & Plot** to load the selected file and render a colour heatmap (time  channel, colour = activity %).
3. Use the Matplotlib toolbar (pan, zoom, etc.) that appears below the plot.
4. Click **Save Image** to export the current heatmap as PNG, JPEG, or PDF.

---

## CSV format

| Column | Description |
|---|---|
| `timestamp` | Board uptime in milliseconds |
| `Ch1`  `Ch126` | Activity level 0100 % for each 1 MHz channel (24012526 MHz) |

---

## Project structure

```
RFmodule/
 main.py                application entry point
 requirements.txt       Python dependencies
 README.md              this file
 moduleTest/
    moduleTest.ino     ESP32 firmware
 saved_data/            recorded CSV files (created automatically)
```
