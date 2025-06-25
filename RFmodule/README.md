# Spectrum Analyzer Visualization

This document explains how to use the Python scripts to visualize the frequency spectrum data collected by your ESP32 with the NRF24L01 module.

## ESP32 Setup

1. Connect your NRF24L01 module to the ESP32:
   - Connect NRF24L01 VCC to 3.3V
   - Connect NRF24L01 GND to GND
   - Connect NRF24L01 CE to GPIO 2
   - Connect NRF24L01 CSN to GPIO 4
   - Connect NRF24L01 SCK to GPIO 18
   - Connect NRF24L01 MOSI to GPIO 23
   - Connect NRF24L01 MISO to GPIO 19

2. Upload the `moduleTest.ino` sketch to your ESP32.

## Collecting and Visualizing Data

### Direct Serial Connection (Recommended)

1. Connect your ESP32 to your computer via USB
2. Open the Serial Monitor at 115200 baud
3. Press 'v' to activate CSV output mode
4. Run the Python visualization script:

```bash
python spectrum_visualizer.py --serial COM3 --samples 100 --save-csv my_spectrum_data.csv
```

Replace `COM3` with your ESP32's serial port (e.g., `/dev/ttyUSB0` on Linux).

### Using Pre-Collected Data

After collecting data, you can visualize it in different ways:

```bash
# Create a static heatmap
python spectrum_visualizer.py --file my_spectrum_data.csv

# Create an animated visualization
python spectrum_visualizer.py --file my_spectrum_data.csv --animate

# Analyze the spectrum data
python spectrum_visualizer.py --file my_spectrum_data.csv --analyze

# Save the visualization to a file
python spectrum_visualizer.py --file my_spectrum_data.csv --output spectrum.png
```

### No Data Yet?

If you haven't collected real data yet, you can generate test data:

```bash
python generate_test_data.py
```

This will create a sample data file with simulated spectrum activity that you can use to test the visualization.

## Installation

### Using Installation Scripts (Recommended)

For Windows users, you can easily install all dependencies by running one of the provided installation scripts:

```
# Using PowerShell
.\install_dependencies.ps1

# OR using Command Prompt
install_dependencies.bat
```

These scripts will check for Python, install all required libraries, and provide guidance on using the tools.

### Manual Installation

If you prefer to install the dependencies manually:

```bash
pip install -r requirements.txt
```

Or install individual packages:

```bash
pip install numpy pandas matplotlib pyserial
```

## ESP32 Commands

The spectrum analyzer responds to the following commands over the serial monitor:

- `s` - Perform a single scan
- `c` - Activate continuous scanning (default)
- `p` - Pause/resume scanning
- `g` - Toggle Serial Plotter mode (for Arduino's built-in plotter)
- `v` - Toggle CSV output mode (for Python visualization)
- `h` - Show help menu
- `r` - Reset the ESP32

## Understanding the Visualization

- The y-axis represents the 126 channels of the NRF24L01, corresponding to frequencies from 2400 MHz to 2525 MHz
- The x-axis represents time, showing how the spectrum activity changes over time
- Brighter/hotter colors indicate higher activity in that frequency range

Common patterns to look for:
- Wi-Fi channels typically appear as blocks of activity (especially around channels 1, 6, and 11)
- Bluetooth devices may appear as frequency-hopping patterns across the spectrum
- Microwave ovens often cause wide-band interference when operating
