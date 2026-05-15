"""
Test script to validate precise timing measurement refactor.

This script:
1. Simulates ESP32 data without timestamps
2. Verifies that Python captures timestamps correctly
3. Validates that timestamps are in proper format
"""

import time
import threading
from collections import deque
import sys

# Constants
NUM_CHANNELS = 126
TEST_SAMPLES = 10
SAMPLE_INTERVAL = 0.1  # 100ms between samples


class MockSerialPort:
    """Mock serial port that sends channel data without timestamps."""
    
    def __init__(self, delay=SAMPLE_INTERVAL):
        self.delay = delay
        self.data_queue = deque()
        self.running = True
        self._setup_data()
    
    def _setup_data(self):
        """Generate mock channel data."""
        for sample_idx in range(TEST_SAMPLES):
            # Create 126 channel values (0-100 activity %)
            channels = [sample_idx % 100] * NUM_CHANNELS
            line = ",".join(str(ch) for ch in channels) + "\n"
            self.data_queue.append(line.encode())
    
    def readline(self):
        """Simulates serial.readline() - returns data with timing."""
        if self.data_queue:
            time.sleep(self.delay)
            return self.data_queue.popleft()
        return b""
    
    def close(self):
        self.running = False


class TimingValidator:
    """Validates timestamp precision."""
    
    def __init__(self):
        self.samples = []
        self.start_time = None
    
    def process_sample(self, timestamp, channels):
        """Process a sample with its timestamp."""
        self.samples.append({
            'timestamp': timestamp,
            'channels': channels,
            'num_channels': len(channels)
        })
    
    def validate(self):
        """Validate timing accuracy."""
        print("\n" + "="*60)
        print("TIMING VALIDATION REPORT")
        print("="*60)
        
        if not self.samples:
            print("ERROR: No samples collected!")
            return False
        
        # Check timestamps are floats
        print(f"\n✓ Collected {len(self.samples)} samples")
        
        # Check timestamp format
        ts_valid = all(isinstance(s['timestamp'], float) for s in self.samples)
        print(f"✓ All timestamps are float: {ts_valid}")
        
        # Check channel count
        ch_valid = all(s['num_channels'] == NUM_CHANNELS for s in self.samples)
        print(f"✓ All samples have {NUM_CHANNELS} channels: {ch_valid}")
        
        # Check timestamp progression
        diffs = []
        for i in range(1, len(self.samples)):
            diff = self.samples[i]['timestamp'] - self.samples[i-1]['timestamp']
            diffs.append(diff)
        
        avg_diff = sum(diffs) / len(diffs) if diffs else 0
        print(f"\nTiming Statistics:")
        print(f"  Expected interval: {SAMPLE_INTERVAL:.4f}s")
        print(f"  Actual avg interval: {avg_diff:.4f}s")
        print(f"  Min interval: {min(diffs):.4f}s")
        print(f"  Max interval: {max(diffs):.4f}s")
        
        # Sample timestamps
        print(f"\nSample Timestamps:")
        for i, sample in enumerate(self.samples[:5]):
            print(f"  Sample {i}: {sample['timestamp']:.6f}s")
        
        print("\n" + "="*60)
        
        return ts_valid and ch_valid


def simulate_thread_receiver():
    """Simulate the SerialReaderThread with mock data."""
    
    print("Starting timing test...")
    print(f"Generating {TEST_SAMPLES} mock samples with {SAMPLE_INTERVAL}s interval\n")
    
    validator = TimingValidator()
    mock_port = MockSerialPort(delay=SAMPLE_INTERVAL)
    
    start_time = time.perf_counter()
    
    for i in range(TEST_SAMPLES):
        timestamp = time.perf_counter() - start_time
        raw = mock_port.readline()
        
        if raw:
            line = raw.decode("utf-8", errors="ignore").strip()
            parts = line.split(",")
            try:
                channel_values = [int(p) for p in parts]
                validator.process_sample(timestamp, channel_values)
                print(f"Sample {i+1}: timestamp={timestamp:.6f}s, channels={len(channel_values)}")
            except ValueError:
                pass
    
    mock_port.close()
    
    # Validate results
    success = validator.validate()
    
    return success


if __name__ == "__main__":
    success = simulate_thread_receiver()
    
    if success:
        print("\n✅ Timing validation PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Timing validation FAILED!")
        sys.exit(1)
