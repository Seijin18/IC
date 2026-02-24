// ===================================================
// NRF24L01 SENDER - ESP32
// ===================================================
// This ESP32 receives commands via Serial and sends them
// to the receiver ESP32 via NRF24L01
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

// Communication address (must match receiver)
const byte address[6] = "00001";

// Message buffer
char message[32];
int messageIndex = 0;

void setup()
{
  // Initialize Serial
  Serial.begin(115200);
  delay(1000);

  // Clear serial buffer
  while (Serial.available())
    Serial.read();

  Serial.println("\n========================================");
  Serial.println("NRF24L01 SENDER - ESP32");
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
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_LOW); // Set power level (LOW, HIGH, MAX)
  radio.setDataRate(RF24_1MBPS); // Set data rate
  radio.setChannel(108);         // Set channel (0-125)
  radio.stopListening();         // Put in TX mode

  Serial.println("Radio configuration:");
  Serial.println("  - Mode: TRANSMITTER");
  Serial.println("  - Channel: 108");
  Serial.println("  - Data Rate: 1Mbps");
  Serial.println("  - Power: LOW");
  Serial.println();
  Serial.println("Ready to send messages!");
  Serial.println("Type a message and press ENTER to send.");
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
  // Check for serial input
  while (Serial.available() > 0)
  {
    char c = Serial.read();

    // If newline or carriage return, send the message
    if (c == '\n' || c == '\r')
    {
      if (messageIndex > 0)
      {
        // Null-terminate the string
        message[messageIndex] = '\0';

        // Send the message
        sendMessage(message);

        // Reset buffer
        messageIndex = 0;
        memset(message, 0, sizeof(message));
      }
    }
    // Add character to buffer (max 31 chars + null terminator)
    else if (messageIndex < 31)
    {
      message[messageIndex++] = c;
    }
  }
}

void sendMessage(const char *msg)
{
  Serial.print("Sending: \"");
  Serial.print(msg);
  Serial.print("\" ... ");

  // Blink LED while sending
  digitalWrite(LED_PIN, HIGH);

  // Send the message
  bool success = radio.write(msg, strlen(msg) + 1);

  digitalWrite(LED_PIN, LOW);

  if (success)
  {
    Serial.println("SUCCESS!");

    // Quick double blink to indicate success
    delay(50);
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(50);
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
  }
  else
  {
    Serial.println("FAILED!");
    Serial.println("Check receiver connection.");

    // Long blink to indicate failure
    digitalWrite(LED_PIN, HIGH);
    delay(500);
    digitalWrite(LED_PIN, LOW);
  }

  Serial.println();
}

// Function to send test message
void sendTestMessage()
{
  const char *testMsg = "TEST";
  Serial.println("Sending test message...");
  sendMessage(testMsg);
}
