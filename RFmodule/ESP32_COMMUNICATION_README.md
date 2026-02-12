# ESP32 NRF24L01 Communication - Sender & Receiver

This project implements bidirectional communication between two ESP32 boards using NRF24L01 radio modules.

## Hardware Requirements

- 2x ESP32 Development Boards
- 2x NRF24L01 Radio Modules (or NRF24L01+PA+LNA for longer range)
- Jumper wires
- USB cables for programming and power

## Wiring Diagram

Both ESP32 boards use the same wiring:

```
NRF24L01    →    ESP32
---------------------------
VCC         →    3.3V
GND         →    GND
CE          →    GPIO 21
CSN         →    GPIO 22
SCK         →    GPIO 18
MOSI        →    GPIO 23
MISO        →    GPIO 19
```

**⚠️ IMPORTANT:**
- Use **3.3V** only (NOT 5V!) - NRF24L01 is not 5V tolerant
- Add a 10µF capacitor between VCC and GND on the NRF24L01 for stable power
- Keep wires short to reduce interference
- For PA+LNA modules, consider using external 3.3V power supply

## Setup Instructions

### 1. Install RF24 Library

In Arduino IDE:
1. Go to **Sketch** → **Include Library** → **Manage Libraries**
2. Search for "RF24"
3. Install "RF24 by TMRh20"

### 2. Upload Sender Code

1. Connect first ESP32 to computer
2. Open `sender_esp32.ino`
3. Select **Board**: "ESP32 Dev Module" (or your ESP32 variant)
4. Select correct **Port**
5. Click **Upload**

### 3. Upload Receiver Code

1. Connect second ESP32 to computer
2. Open `receiver_esp32.ino`
3. Select **Board**: "ESP32 Dev Module"
4. Select correct **Port**
5. Click **Upload**

## Usage

### Sender ESP32

1. Open Serial Monitor (115200 baud)
2. Type a message
3. Press ENTER to send
4. LED will blink during transmission:
   - **Quick double blink**: Message sent successfully
   - **Long blink**: Transmission failed

**Example:**
```
Type: Hello World
LED blinks → Message sent
```

### Receiver ESP32

1. Open Serial Monitor (115200 baud)
2. Wait for messages
3. When message received:
   - **LED blinks 3 times**
   - Message displayed on Serial Monitor

**Example Output:**
```
========================================
MESSAGE RECEIVED!
Content: "Hello World"
Length: 11 characters
Time: 45 seconds since boot
========================================
```

## LED Indicator Meanings

### Sender
- **3 blinks at startup**: Ready to send
- **Double blink**: Message sent successfully
- **Long blink**: Transmission failed
- **Rapid blinking at startup**: NRF24L01 initialization error

### Receiver
- **3 blinks at startup**: Ready to receive
- **3 blinks**: Message received
- **Rapid blinking at startup**: NRF24L01 initialization error

## Testing Steps

1. **Power on both ESP32s**
   - Both should blink 3 times indicating they're ready

2. **Open both Serial Monitors**
   - Sender: 115200 baud
   - Receiver: 115200 baud

3. **Send a test message**
   - Type "TEST" in sender's Serial Monitor
   - Press ENTER
   - Sender LED should double-blink
   - Receiver LED should blink 3 times
   - Receiver Serial Monitor should show the message

4. **Send more messages**
   - Try different messages
   - Maximum 31 characters per message

## Troubleshooting

### Problem: "NRF24L01 not detected"
**Solutions:**
- Check all wiring connections
- Verify 3.3V power (NOT 5V!)
- Add 10µF capacitor between VCC and GND
- Try different NRF24L01 module (they can be defective)
- Reduce wire length

### Problem: "Message FAILED"
**Solutions:**
- Ensure both ESP32s are powered on
- Check that receiver is running
- Verify both use same channel (108) and address
- Reduce distance between modules
- Check for interference (WiFi routers, etc.)

### Problem: LED doesn't blink
**Solutions:**
- Check GPIO2 is available (some boards use it differently)
- Verify LED_PIN definition matches your board
- Test with external LED on GPIO2 if built-in doesn't work

### Problem: Garbled messages
**Solutions:**
- Reduce transmission distance
- Add capacitor to NRF24L01 power
- Lower data rate in code: `radio.setDataRate(RF24_250KBPS);`
- Increase power level: `radio.setPALevel(RF24_PA_HIGH);`

## Customization

### Change Communication Channel
Edit in both files:
```cpp
radio.setChannel(108);  // Change to 0-125
```

### Change Communication Address
Edit in both files:
```cpp
const byte address[6] = "00001";  // Change to any 5-character string
```

### Change Number of LED Blinks
In `receiver_esp32.ino`:
```cpp
const int BLINKS_PER_MESSAGE = 3;  // Change to desired number
```

### Increase Range
In both files:
```cpp
radio.setPALevel(RF24_PA_HIGH);  // or RF24_PA_MAX for maximum range
```

### Change Message Size
Edit in both files:
```cpp
char message[32];  // Change 32 to desired size (max 32 for NRF24L01)
```

## Advanced Features You Can Add

1. **Acknowledge Messages**: Send confirmation back from receiver to sender
2. **Bidirectional**: Allow receiver to also send messages
3. **Multiple Receivers**: Broadcast to multiple ESP32s
4. **Encrypted Messages**: Add encryption for security
5. **Message Queue**: Buffer multiple messages
6. **RSSI Display**: Show signal strength
7. **Auto-retry**: Automatically resend failed messages

## Technical Specifications

- **Frequency**: 2.4 GHz ISM band
- **Data Rate**: 1 Mbps (configurable: 250kbps, 1Mbps, 2Mbps)
- **Channel**: 108 (configurable: 0-125)
- **Max Payload**: 32 bytes
- **Range**: 
  - Standard NRF24L01: ~10-30 meters indoor
  - NRF24L01+PA+LNA: ~100-500 meters outdoor
- **Power Levels**: MIN, LOW, HIGH, MAX

## Safety Notes

⚠️ **Power Supply**: Always use 3.3V for NRF24L01
⚠️ **Antenna**: Don't operate PA+LNA modules without antenna attached
⚠️ **Interference**: May interfere with WiFi on same channel

## License

This code is provided as-is for educational purposes.

## Support

For issues or questions:
1. Check wiring diagram
2. Verify library installation
3. Test with simple messages first
4. Check Serial Monitor for error messages