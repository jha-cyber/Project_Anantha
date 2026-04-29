# Project_Anantha
Anantha is a snake bot which can be used for search operations during Earthquakes and Landslide in confined spaces providing real video feed.


# Components Used
1. ESP32
2. ESP32 CAM Module
3. SG90 Servo Motor(6 units)
4. USB to TTL Converter
5. 12 Volt Power Supply
6. LM2596S Buck Converter



# Functionality
1. Real Time Video Monitoring using esp32 cam module
2. Real time object identification using YOLOv8 Model
3. Slither movement to move across bumpy obstacles.
4. Wireless Control System using wifi



# Circuit Connections
  **Power Distribution**
  1. 12V(+)                    ----->           LM2596S(IN+)
  2. 12V(-)                    ----->           LM2596S(IN-)
  3. LM2596S(OUT+)             ----->           5 Volt Rail 
  4. LM2596S(OUT-)             ----->           Ground Rail 
  5. Servo 1,3,5(Red Wire)     ----->           5 Volt Rail
  6. Servo 1,3,5(Brown Wire)   ----->           Ground Rail
  
  **ESP32 Main**
  1. 5V      -----> 5V Rail line
  2. GND     -----> Ground Rail line
  3. Pin 13  -----> Servo 1(Yellow Wire)
  4. Pin 27  -----> Servo 3(Yellow Wire)
  5. Pin 25  -----> Servo 5(Yellow Wire)
  _NOTE- The servos are numbered 1,2,3,4,5,6 from tail to head and the alternate servos are connected to esp32 so that it can create a Slither movement using the    servos which move in the same plane, in our case it's vertical so that we can get the bot to move in a sinusodial wave manner._
  
  **ESP32-CAM**
  5V      -----> 5V Rail line
  GND     -----> Ground Rail line
  (No data wire connects to the Main ESP32,as the ESP32 Cam Module communicates via Wi-Fi on it's own)

  **USB to TTL Converter (Only for uploading code to Camera)**
  5V      -----> ESP32-CAM 5V
  GND     -----> ESP32-CAM GND
  TX      -----> ESP32-CAM U0RX
  RX      -----> ESP32-CAM U0TX
  _NOTE - ESP32-CAM IO0 ------> GND(while uploading the code only)_

  _NOTE - To know about the camera module in your ESP32 CAM visit the official repository ---> https://github.com/espressif/esp32-camera_


# Software Stack
1.Arduino IDE(C++)
2.Python 3.14.3
3.OpenCV
4.YOLOv8(Ultralytics)


**First Year Engineering Project made by Vikas Jha**





  
