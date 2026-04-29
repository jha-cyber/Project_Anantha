/**
 * Project Anantha: Spinal Cord (Motor Control)
 * =========================================================
 * Target Hardware: ESP32 Dev Module
 * Actuators: 3x SG90 Micro Servos
 * * Description: 
 * Acts as the spinal cord of the robot. Receives autonomous 
 * directional commands via Bluetooth from the Python AI Ground 
 * Station and translates them into a continuous sinusoidal 
 * slithering gait.
 * * Required Libraries:
 * - ESP32Servo (by Kevin Harrington, John K. Bennett)
 */

#include <ESP32Servo.h>
#include "BluetoothSerial.h"

// ==========================================
// 1. BLUETOOTH SETUP
// ==========================================
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please update your ESP32 board manager.
#endif

BluetoothSerial SerialBT;
bool isMoving = false; // The bot starts in "Park"

// ==========================================
// 2. HARDWARE MAPPING (3 Active Segments)
// ==========================================
const int NUM_ACTIVE = 3;
Servo activeServos[NUM_ACTIVE];

// The GPIO pins connected to the servo data wires
int activePins[NUM_ACTIVE] = {13, 25, 27}; 

// ==========================================
// 3. GAIT PHYSICS (Sinusoidal Wave)
// ==========================================
float amplitude = 45.0;      // How wide the snake swings (degrees)
float spatialFreq = 0.8;     // How tight the S-curves are
float temporalFreq = 2.5;    // How fast the wave moves down the body
int centerAngle = 90;        // Center point for the servos

void setup() {
  Serial.begin(115200);
  
  // Start the Bluetooth Broadcast
  SerialBT.begin("Project-Anantha"); 
  Serial.println("[SYSTEM] Bluetooth Started! Ready to pair.");

  // Allocate hardware timers for smooth PWM signals
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  // Initialize and center the active motors
  for (int i = 0; i < NUM_ACTIVE; i++) {
    activeServos[i].setPeriodHertz(50); // Standard 50Hz for SG90
    activeServos[i].attach(activePins[i], 500, 2400);
    activeServos[i].write(centerAngle);
  }

  delay(3000); 
  Serial.println("[SYSTEM] Spinal Cord Online. Waiting for AI Commands...");
}

void loop() {
  // ----------------------------------------
  // LISTEN FOR BLUETOOTH COMMANDS
  // ----------------------------------------
  if (SerialBT.available()) {
    char cmd = SerialBT.read();
    
    if (cmd == 'W' || cmd == 'w' || cmd == 'F' || cmd == 'f') {
      isMoving = true;
      SerialBT.println("[CMD] SLITHER FORWARD");
    }
    else if (cmd == 'S' || cmd == 's') {
      isMoving = false;
      SerialBT.println("[CMD] ALL STOP");
      
      // Snap back to center when stopped
      for (int i = 0; i < NUM_ACTIVE; i++) {
        activeServos[i].write(centerAngle);
      }
    }
  }

  // ----------------------------------------
  // NON-BLOCKING LOCOMOTION
  // ----------------------------------------
  if (isMoving) {
    float timeSec = millis() / 1000.0;

    for (int i = 0; i < NUM_ACTIVE; i++) {
      // Calculate the current angle based on a traveling sine wave
      float offset = amplitude * sin(spatialFreq * i + timeSec * temporalFreq);
      float targetAngle = centerAngle + offset;
      
      // Command the servo
      activeServos[i].write(targetAngle);
    }
  }

  // Small delay for physical mechanical limits
  delay(15); 
}
