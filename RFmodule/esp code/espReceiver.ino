/*
 * NRF24L01 Spectrum Reader
 *
 * Continuously scans all 126 channels of the 2.4 GHz band and sends
 * one CSV line per scan over the serial port at 115200 baud.
 *
 * Scan strategy: for each channel, settle once then sample N times in place.
 * This is ~50× faster than the sweep-per-sample approach.
 *
 * Output format (no header line):
 *   <timestamp_ms>,<ch0_%>,<ch1_%>,...,<ch125_%>
 *
 * Wiring (NRF24L01 → ESP32):
 *   VCC  → 3.3 V      GND  → GND
 *   CE   → GPIO 21    CSN  → GPIO 22
 *   SCK  → GPIO 18    MOSI → GPIO 23    MISO → GPIO 19
 */

#include <Arduino.h>
#include <SPI.h>
#include <RF24.h>

#define CE_PIN  21
#define CSN_PIN 22

RF24 radio(CE_PIN, CSN_PIN);

const int NUM_CHANNELS  = 126;  // channels 0-125 → 2400-2525 MHz
const int SCAN_SAMPLES  = 30;  // carrier-detect passes per channel (per-channel sampling)

int channelData[NUM_CHANNELS];

// ---------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);

  // Give the NRF24L01 power supply time to stabilise before touching SPI.
  delay(2000);

  SPI.begin();

  // Retry radio init up to 5 times; some modules need more than one attempt.
  bool radioOK = false;
  for (int attempt = 1; attempt <= 5; attempt++) {
    if (radio.begin()) {
      radioOK = true;
      break;
    }
    Serial.print("radio.begin() failed, attempt ");
    Serial.print(attempt);
    Serial.println("/5 – retrying in 500 ms…");
    delay(500);
  }

  if (!radioOK) {
    while (true) {
      Serial.println("ERROR: NRF24L01 not detected. Check wiring.");
      delay(3000);
    }
  }

  radio.setAutoAck(false);
  radio.stopListening();
  radio.setPALevel(RF24_PA_MIN);
  radio.setDataRate(RF24_1MBPS);

  Serial.println("NRF24L01 ready. Scanning…");
}

// ---------------------------------------------------------------------------
void scanSpectrum() {
  for (int ch = 0; ch < NUM_CHANNELS; ch++) {
    radio.setChannel(ch);
    delayMicroseconds(130);  // PLL settling time (datasheet minimum)

    int hits = 0;
    for (int s = 0; s < SCAN_SAMPLES; s++) {
      radio.startListening();
      delayMicroseconds(130);  // NRF24L01 requires ≥130 µs in RX before CD bit is valid
      if (radio.testCarrier()) hits++;
      radio.stopListening();
    }

    channelData[ch] = (hits * 100) / SCAN_SAMPLES;
  }
}

// ---------------------------------------------------------------------------
void sendCSV() {
  Serial.print(millis());
  for (int i = 0; i < NUM_CHANNELS; i++) {
    Serial.print(',');
    Serial.print(channelData[i]);
  }
  Serial.println();
}

// ---------------------------------------------------------------------------
void loop() {
  scanSpectrum();
  sendCSV();
}
