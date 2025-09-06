// Pins
// CE: 2
// CSN: 4
// SCK: 18
// MOSI: 23
// MISO: 19

#include <Arduino.h>
#include <SPI.h>
#include <RF24.h>

// Pin definitions for ESP32
#define CE_PIN 22
#define CSN_PIN 21

// Initialize NRF24L01
RF24 radio(CE_PIN, CSN_PIN);

// Frequency spectrum variables
const int NUM_CHANNELS = 126;  // NRF24L01 has 126 channels (0-125)
int spectrum[NUM_CHANNELS];    // Array to store signal strength for each channel
int channelData[NUM_CHANNELS]; // Array to store averaged data
const int SCAN_SAMPLES = 100;  // Number of samples per channel for averaging

// Timing variables
unsigned long lastScanTime = 0;
const unsigned long SCAN_INTERVAL = 1000; // Scan every 1 second
bool scanningEnabled = true; // Flag to control pause/resume
bool plotterMode = false;    // Flag for Serial Plotter output
bool csvMode = false;        // Flag for CSV output mode

void setup() {
  // Try different baud rates to ensure compatibility
  Serial.begin(115200);
  delay(500);
  
  // Reset the serial connection
  Serial.end();
  delay(100);
  Serial.begin(115200);
  delay(1000);
  
  // Clear serial buffer
  while(Serial.available()) Serial.read();
  
  // Wait for serial connection to establish
  while (!Serial) {
    ; // wait for serial port to connect
  }
  
  // Send test pattern to help diagnose issues
  // Serial.println("\n\n\n");
  // Serial.println("===========================================");
  // Serial.println("NRF24L01 Frequency Spectrum Analyzer");
  // Serial.println("Baud Rate: 115200");
  // Serial.println("If you see this message clearly, serial is working!");
  // Serial.println("===========================================");
  
  // Initialize SPI
  SPI.begin();
  
  // Initialize radio
  if (!radio.begin()) {
    Serial.println("Error: NRF24L01 not detected! Check wiring.");
    while (1) {
      delay(1000);
    }
  }
  
  // Configure radio for spectrum analysis
  radio.setAutoAck(false);          // Disable auto acknowledgment
  radio.stopListening();            // Put radio in TX mode
  radio.setPALevel(RF24_PA_MIN);    // Set power to minimum for better sensitivity
  radio.setDataRate(RF24_1MBPS);    // Set data rate to 1Mbps
  
  Serial.println("NRF24L01 initialized successfully!");
  Serial.println("Starting frequency spectrum scan...");
  Serial.println("Frequency range: 2400-2525 MHz (126 channels)");
  Serial.println();
  
  // Print header
  // printHeader();
}

// void loop() {
//   unsigned long currentTime = millis();
  
//   if (scanningEnabled && (currentTime - lastScanTime >= SCAN_INTERVAL)) {
//     scanSpectrum();
    
//     if (csvMode) {
//       outputCSVData();
//     } else {
//       displaySpectrum();
//     }
    
//     lastScanTime = currentTime;
//   }
  
//   // Check for serial commands
//   if (Serial.available()) {
//     handleSerialCommands();
//   }
// }

void loop() {
  unsigned long currentTime = millis();
  
  if (scanningEnabled && (currentTime - lastScanTime >= SCAN_INTERVAL)) {
    scanSpectrum();
    outputCSVData();
    lastScanTime = currentTime;
  }
}

void scanSpectrum() {
  // if (!plotterMode) {
  //   Serial.print("Scanning");
  // }
  
  // Clear arrays
  for (int i = 0; i < NUM_CHANNELS; i++) {
    spectrum[i] = 0;
    channelData[i] = 0;
  }
  
  // Scan each channel multiple times for averaging
  for (int sample = 0; sample < SCAN_SAMPLES; sample++) {
    for (int channel = 0; channel < NUM_CHANNELS; channel++) {
      // Set channel
      radio.setChannel(channel);
      delayMicroseconds(130); // Allow settling time
      
      // Start listening
      radio.startListening();
      delayMicroseconds(130);
      
      // Check for carrier
      if (radio.testCarrier()) {
        spectrum[channel]++;
      }
      
      radio.stopListening();
    }
    
    // // Progress indicator
    // if (!plotterMode && sample % 10 == 0) {
    //   Serial.print(".");
    // }
  }
  
  // if (!plotterMode) {
  //   Serial.println(" Done!");
  // }
  
  // Calculate averages and convert to percentage
  for (int i = 0; i < NUM_CHANNELS; i++) {
    channelData[i] = (spectrum[i] * 100) / SCAN_SAMPLES;
  }
}

void displaySpectrum() {
  if (plotterMode) {
    // Format for Serial Plotter - simplified to avoid overwhelming the plotter
    // Instead of trying to plot all 126 channels with labels, just output raw values
    for (int i = 0; i < NUM_CHANNELS; i++) {
      Serial.print(channelData[i]);
      if (i < NUM_CHANNELS - 1) {
        Serial.print(" ");  // Space delimiter works better for Serial Plotter
      }
    }
    Serial.println();
  } else {
    // Regular text display mode
    Serial.println("\n=== Frequency Spectrum Analysis ===");
    Serial.println("Ch# | Freq(MHz) | Activity | Bar Graph");
    Serial.println("----|-----------|----------|----------");
    
    for (int i = 0; i < NUM_CHANNELS; i++) {
      int frequency = 2400 + i; // Calculate frequency in MHz
      
      Serial.printf("%3d | %4d      | %3d%%     | ", i, frequency, channelData[i]);
      
      // Create bar graph
      int barLength = channelData[i] / 5; // Scale for display (20% = 4 chars)
      for (int j = 0; j < barLength && j < 20; j++) {
        Serial.print("#"); // Using standard ASCII character instead of Unicode
      }
      
      // Highlight high activity channels
      if (channelData[i] > 50) {
        Serial.print(" << HIGH ACTIVITY");
      } else if (channelData[i] > 20) {
        Serial.print(" << MODERATE");
      }
      
      Serial.println();
    }
    
    // Find and display peak channels
    findPeakChannels();
    Serial.println("\n==================================================");
  }
}

void findPeakChannels() {
  Serial.println("\n--- Peak Activity Channels ---");
  
  // Find channels with significant activity
  bool foundPeaks = false;
  for (int i = 0; i < NUM_CHANNELS; i++) {
    if (channelData[i] > 10) { // Threshold for significant activity
      int frequency = 2400 + i;
      Serial.printf("Channel %d (%d MHz): %d%% activity\n", i, frequency, channelData[i]);
      foundPeaks = true;
    }
  }
  
  if (!foundPeaks) {
    Serial.println("No significant activity detected on any channel.");
  }
}

void printHeader() {
  Serial.println("Commands:");
  Serial.println("'s' - Single scan");
  Serial.println("'c' - Continuous scanning (default)");
  Serial.println("'p' - Pause/resume scanning");
  Serial.println("'g' - Toggle Serial Plotter graph mode");
  Serial.println("'v' - Toggle CSV output mode (for Python visualization)");
  Serial.println("'h' - Show this help");
  Serial.println("'r' - Reset and restart");
  Serial.println();
}

void handleSerialCommands() {
  char command = Serial.read();
  
  switch (command) {
    case 's':
    case 'S':
      Serial.println("Performing single scan...");
      scanSpectrum();
      displaySpectrum();
      break;
      
    case 'c':
    case 'C':
      scanningEnabled = true;
      Serial.println("Continuous scanning mode activated.");
      break;
      
    case 'p':
    case 'P':
      scanningEnabled = !scanningEnabled;
      if (scanningEnabled) {
        Serial.println("Scanning resumed.");
      } else {
        Serial.println("Scanning paused. Send 'p' again to resume or 'c' to restart continuous mode.");
      }
      break;
      
    case 'g':
    case 'G':
      // Don't allow both plotter and CSV modes simultaneously
      if (csvMode) {
        Serial.println("Please disable CSV mode first with 'v'");
        break;
      }
      
      plotterMode = !plotterMode;
      if (plotterMode) {
        // Clear the serial output before switching to plotter mode
        for (int i = 0; i < 10; i++) {
          Serial.println();
        }
        Serial.println("Serial Plotter mode activated. Open Serial Plotter to see the graph.");
        Serial.println("Send 'g' again to return to text mode.");
      } else {
        Serial.println("\n\nReturning to text mode...");
        printHeader();
      }
      break;
      
    case 'v':
    case 'V':
      // Don't allow both plotter and CSV modes simultaneously
      if (plotterMode) {
        Serial.println("Please disable plotter mode first with 'g'");
        break;
      }
      
      csvMode = !csvMode;
      if (csvMode) {
        Serial.println("CSV output mode activated for Python visualization.");
        Serial.println("Data will be output in CSV format. Send 'v' again to return to text mode.");
        
        // Output CSV header row
        Serial.print("timestamp");
        for (int i = 0; i < NUM_CHANNELS; i++) {
          Serial.print(",ch");
          Serial.print(i);
        }
        Serial.println();
      } else {
        Serial.println("\n\nReturning to text mode...");
        printHeader();
      }
      break;
      
    case 'h':
    case 'H':
      printHeader();
      break;
      
    case 'r':
    case 'R':
      Serial.println("Restarting...");
      ESP.restart();
      break;
      
    default:
      // Ignore unknown commands
      break;
  }
  
  // Clear any remaining characters
  while (Serial.available()) {
    Serial.read();
  }
}

// Function to get channel with highest activity
int getMaxActivityChannel() {
  int maxChannel = 0;
  int maxActivity = 0;
  
  for (int i = 0; i < NUM_CHANNELS; i++) {
    if (channelData[i] > maxActivity) {
      maxActivity = channelData[i];
      maxChannel = i;
    }
  }
  
  return maxChannel;
}

// Function to get average activity across all channels
float getAverageActivity() {
  long total = 0;
  
  for (int i = 0; i < NUM_CHANNELS; i++) {
    total += channelData[i];
  }
  
  return (float)total / NUM_CHANNELS;
}

// Function to count active channels above threshold
int countActiveChannels(int threshold) {
  int count = 0;
  
  for (int i = 0; i < NUM_CHANNELS; i++) {
    if (channelData[i] > threshold) {
      count++;
    }
  }
  
  return count;
}

// Function to output data in CSV format to serial port
void outputCSVData() {
  // Output timestamp and all channel data in CSV format
  // Format: timestamp,ch0,ch1,ch2,...,ch125
  
  // Start with timestamp (milliseconds since start)
  Serial.print(millis());
  
  // Add all channel data
  for (int i = 0; i < NUM_CHANNELS; i++) {
    Serial.print(",");
    Serial.print(channelData[i]);
  }
  
  Serial.println();
}
