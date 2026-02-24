// ===================================================
// NRF24L01 RECEIVER - ESP32
// ===================================================
// This ESP32 receives messages from the sender ESP32
// via NRF24L01, blinks its LED, and displays the message
// on the Serial Monitor
//
// Wiring for NRF24L01:
// CE:   GPIO 21
// CSN:  GPIO 22
// SCK:  GPIO 18
// MOSI: GPIO 23
// MISO: GPIO 19
// VCC:  3.3V
// GND:  GND
// ===================================================

#include <SPI.h>
#include <RF24.h>

// Pin definitions
#define CE_PIN 21
#define CSN_PIN 22
#define LED_PIN 2 // Built-in LED

// Initialize NRF24L01
RF24 radio(CE_PIN, CSN_PIN);

// Communication address (must match sender)
const byte address[6] = "00001";

// Message buffer
char receivedMessage[32];

// LED blink control
unsigned long lastBlinkTime = 0;
int blinkCount = 0;
bool ledState = false;
const int BLINKS_PER_MESSAGE = 3; // Number of blinks when message received

void setup()
{
  // Initialize Serial
  Serial.begin(115200);
  delay(1000);

  // Clear serial buffer
  while (Serial.available())
    Serial.read();

  Serial.println("\n========================================");
  Serial.println("NRF24L01 RECEIVER - ESP32");
  Serial.println("========================================");

  // Initialize built-in LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Initialize SPI
  SPI.begin();

  // Initialize radio
  if (!radio.begin())
  {
    Serial.println("ERROR: NRF24L01 not detected!");
    Serial.println("Check wiring and connections.");
    while (1)
    {
      // Blink LED rapidly to indicate error
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
      delay(100);
    }
  }

  Serial.println("NRF24L01 initialized successfully!");

  // Configure radio
  radio.openReadingPipe(0, address);
  radio.setPALevel(RF24_PA_LOW); // Set power level (LOW, HIGH, MAX)
  radio.setDataRate(RF24_1MBPS); // Set data rate
  radio.setChannel(108);         // Set channel (0-125) - must match sender
  radio.startListening();        // Put in RX mode

  Serial.println("Radio configuration:");
  Serial.println("  - Mode: RECEIVER");
  Serial.println("  - Channel: 108");
  Serial.println("  - Data Rate: 1Mbps");
  Serial.println("  - Power: LOW");
  Serial.println();
  Serial.println("Listening for messages...");
  Serial.println("========================================\n");

  // Blink LED 3 times to indicate ready
  for (int i = 0; i < 3; i++)
  {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
}

void loop()
{
  // Check if there's data available
  if (radio.available())
  {
    // Read the message
    memset(receivedMessage, 0, sizeof(receivedMessage));
    radio.read(&receivedMessage, sizeof(receivedMessage));

    // Display received message
    Serial.println("========================================");
    Serial.println("MESSAGE RECEIVED!");
    Serial.print("Content: \"");
    Serial.print(receivedMessage);
    Serial.println("\"");
    Serial.print("Length: ");
    Serial.print(strlen(receivedMessage));
    Serial.println(" characters");
    Serial.print("Time: ");
    Serial.print(millis() / 1000);
    Serial.println(" seconds since boot");
    Serial.println("========================================\n");

    // Start blinking LED
    blinkCount = 0;
    blinkLED();
  }

  // Handle LED blinking
  if (blinkCount > 0 && blinkCount < BLINKS_PER_MESSAGE * 2)
  {
    unsigned long currentTime = millis();
    if (currentTime - lastBlinkTime >= 200)
    { // 200ms per blink state
      lastBlinkTime = currentTime;
      ledState = !ledState;
      digitalWrite(LED_PIN, ledState ? HIGH : LOW);
      blinkCount++;
    }
  }
  else if (blinkCount >= BLINKS_PER_MESSAGE * 2)
  {
    // Ensure LED is off after blinking
    digitalWrite(LED_PIN, LOW);
    blinkCount = 0;
  }
}

void blinkLED()
{
  // Initialize blinking sequence
  blinkCount = 1;
  lastBlinkTime = millis();
  ledState = true;
  digitalWrite(LED_PIN, HIGH);
}

// Function to print radio details (for debugging)
void printRadioDetails()
{
  Serial.println("\n--- Radio Details ---");
  radio.printDetails();
  Serial.println("-------------------\n");
}
