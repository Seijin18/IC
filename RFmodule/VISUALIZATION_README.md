# RF Spectrum Time Series Visualization

This document describes the new time series visualization capabilities added to the RF module project.

## New Files Added

### 1. `time_series_visualizer.py`
A comprehensive GUI application for visualizing RF spectrum data over time.

**Features:**
- Load multiple CSV files from the saved_data directory
- Animated heatmap with time navigation slider
- Channel-specific time series plots
- Device comparison visualizations
- Interactive GUI with configuration options

**Usage:**
```bash
# Run GUI mode
python time_series_visualizer.py

# Command line mode
python time_series_visualizer.py /path/to/data/directory heatmap
python time_series_visualizer.py /path/to/data/directory timeseries
```

### 2. `quick_visualizer.py`
A command-line tool for quick visualization and batch processing.

**Features:**
- Generate overview heatmaps of all data
- Channel comparison plots
- Device summary statistics
- Batch processing with output to files
- No GUI required - perfect for automation

**Usage:**
```bash
# Basic usage (uses saved_data directory)
python quick_visualizer.py

# Specify data directory
python quick_visualizer.py /path/to/data

# Save outputs without showing plots
python quick_visualizer.py --output-dir ./plots --no-show

# Only generate heatmap
python quick_visualizer.py --heatmap-only

# Specify channels for time series
python quick_visualizer.py --channels "1,6,11,20,40"

# Full example
python quick_visualizer.py ./saved_data --output-dir ./analysis_results --channels "1,6,11,40,80"
```

### 3. Updated `interface.py`
The existing interface now includes a "Open Time Series Visualizer" button that opens the time series visualization window.

## Visualization Types

### 1. Overview Heatmap
- Shows RF activity across all 126 channels over time
- Color-coded intensity (blue=low, red=high)
- WiFi channels (1, 6, 11) marked with white dashed lines
- Time progression on X-axis, frequency channels on Y-axis

### 2. Animated Heatmap with Slider
- Interactive heatmap with time navigation
- Configurable time window size
- Real-time title updates showing current time range
- Ideal for detailed analysis of specific time periods

### 3. Channel Time Series
- Line plots for specific channels over time
- Configurable channel selection
- Shows activity trends and patterns
- Useful for analyzing specific frequency behaviors

### 4. Device Comparison
- Side-by-side heatmaps for different devices
- Automatic device detection from filenames
- Helps identify device-specific RF signatures
- Statistical summaries for each device

### 5. Device Summary Statistics
- Average activity by channel and device
- Total activity over time
- Recording duration comparison
- Activity distribution charts

## Data Format

The visualizers work with CSV files containing:
- `timestamp` column (in milliseconds)
- `Ch1` to `Ch126` columns (RF activity values)
- Automatic device detection from filenames in format: `(device_name) filename.csv`

## Configuration Options

### Time Series Visualizer GUI:
- **Time Window Size**: Number of time points to display in animated heatmap
- **Channels**: Comma-separated list of channels for time series plots

### Quick Visualizer Command Line:
- `--output-dir`: Directory to save generated plots
- `--channels`: Channels to include in time series analysis
- `--heatmap-only`: Generate only the overview heatmap
- `--no-show`: Save plots without displaying them

## Examples

### Analyzing WiFi Interference
```bash
python quick_visualizer.py --channels "1,6,11" --output-dir ./wifi_analysis
```

### Complete Analysis with Outputs
```bash
python quick_visualizer.py ./saved_data --output-dir ./complete_analysis
```

### Quick Overview
```bash
python quick_visualizer.py --heatmap-only
```

## Tips for Analysis

1. **WiFi Channel Analysis**: Focus on channels 1, 6, and 11 to analyze WiFi activity
2. **Device Fingerprinting**: Use device comparison to identify unique RF signatures
3. **Time-based Patterns**: Use animated heatmaps to spot temporal patterns
4. **Interference Detection**: Look for unexpected activity outside normal device channels
5. **Performance Monitoring**: Use total activity plots to monitor overall RF environment

## Technical Notes

- **Memory Usage**: Large datasets may require reducing time window size
- **Performance**: Quick visualizer is optimized for batch processing
- **File Format**: All CSV files in the target directory will be loaded automatically
- **Color Mapping**: Custom colormap designed for RF spectrum visualization
- **Time Conversion**: Timestamps automatically converted from milliseconds to seconds

## Integration with Existing Workflow

The visualization tools integrate seamlessly with the existing RF data collection interface:

1. Collect data using the main interface
2. Data is automatically saved to `saved_data/` directory
3. Use "Open Time Series Visualizer" button for interactive analysis
4. Use `quick_visualizer.py` for batch analysis and report generation

This provides a complete workflow from data collection to analysis and visualization.
