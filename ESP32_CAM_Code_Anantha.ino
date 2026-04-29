#include "esp_camera.h"
#include <WiFi.h>
#include "img_converters.h" // WE NEED THIS TO SOFTWARE-ENCODE THE VIDEO!

// ========== ENTER YOUR WI-FI HERE ==========
const char* ssid = "Your_Wifi_Name";
const char* password = "Your_Wifi_Password";
// ===========================================

// Standard AI Thinker ESP32-CAM Pins
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

WiFiServer server(81);

void setup() {
  Serial.begin(115200);
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 10000000; // Slowed down for the GC2145
  
  // ========================================================
  // THE GC2145 OVERRIDE PROTOCOL
  // ========================================================
  config.pixel_format = PIXFORMAT_RGB565; // Ask for raw pixels, NOT JPEG!
  config.frame_size = FRAMESIZE_QVGA;     // Keep resolution at 320x240 so the CPU doesn't melt
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // Initialize the Camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.println("Connecting to Wi-Fi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  Serial.println("");
  Serial.println("GC2145 Camera Online!");
  Serial.print("Stream URL: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":81/stream");

  server.begin();
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    String request = client.readStringUntil('\r');
    if (request.indexOf("/stream") != -1) {
      client.println("HTTP/1.1 200 OK");
      client.println("Content-Type: multipart/x-mixed-replace; boundary=frame");
      client.println();

      while (client.connected()) {
        camera_fb_t * fb = esp_camera_fb_get();
        if (!fb) break;

        uint8_t * _jpg_buf = NULL;
        size_t _jpg_buf_len = 0;

        // Software JPEG Compression (The ESP32 CPU does the work here)
        bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
        esp_camera_fb_return(fb); // Free the raw frame immediately

        if (jpeg_converted && _jpg_buf != NULL) {
          client.print("--frame\r\n");
          client.print("Content-Type: image/jpeg\r\n");
          client.print("Content-Length: ");
          client.print(_jpg_buf_len);
          client.print("\r\n\r\n");
          client.write(_jpg_buf, _jpg_buf_len);
          client.print("\r\n");
          
          free(_jpg_buf); // Clean up the memory
        }
      }
    }
    client.stop();
  }
}
