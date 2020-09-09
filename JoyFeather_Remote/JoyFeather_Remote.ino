#include "WiFi.h"
#include "WiFiUdp.h"
#include "Adafruit_seesaw.h"

const char* ssid = "MyWiFi";
const char* password =  "WiFiPass";

const char* host = "192.168.1.1";
const int port = 9999;

//WiFiClient client;
WiFiUDP Udp;

Adafruit_seesaw ss;

#define BUTTON_RIGHT 6
#define BUTTON_DOWN  7
#define BUTTON_LEFT  9
#define BUTTON_UP    10
#define BUTTON_SEL   14
uint32_t button_mask = (1 << BUTTON_RIGHT) | (1 << BUTTON_DOWN) | 
                (1 << BUTTON_LEFT) | (1 << BUTTON_UP) | (1 << BUTTON_SEL);

#if defined(ESP8266)
  #define IRQ_PIN   2
#elif defined(ESP32)
  #define IRQ_PIN   14
#elif defined(ARDUINO_NRF52832_FEATHER)
  #define IRQ_PIN   27
#elif defined(TEENSYDUINO)
  #define IRQ_PIN   8
#elif defined(ARDUINO_ARCH_WICED)
  #define IRQ_PIN   PC5
#else
  #define IRQ_PIN   5
#endif


void setup() {
 
  Serial.begin(115200);
  while(!Serial) {
    delay(10);
  }

  if(!ss.begin(0x49)){
    Serial.println("ERROR! seesaw not found");
    while(1);
  } else {
    Serial.println("seesaw started");
    Serial.print("version: ");
    Serial.println(ss.getVersion(), HEX);
  }
  ss.pinModeBulk(button_mask, INPUT_PULLUP);
  ss.setGPIOInterrupts(button_mask, 1);

  pinMode(IRQ_PIN, INPUT);
 
  WiFi.begin(ssid, password);
 
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi..");
  }
 
  Serial.println("Connected to the WiFi network");

   
}

int last_x = 0, last_y = 0;


void sendPacket(uint16_t x, uint16_t y, uint32_t buttons) {

  
    // Not sent until endPackage has been called
    Udp.beginPacket(host, port);
    Udp.write(0xff);
    Udp.write(0xff);
    Udp.write(x >> 8);
    Udp.write(x);
    Udp.write(y >> 8);
    Udp.write(y);
    Udp.write(buttons >> 8);
    Udp.write(buttons);
    Udp.endPacket();
  
}



void loop() {
  // put your main code here, to run repeatedly:
  uint16_t x = ss.analogRead(3);
  uint16_t y = ss.analogRead(2);
  
  if ( (abs(x - last_x) > 3)  ||  (abs(y - last_y) > 3)) {
    Serial.print(x); Serial.print(", "); Serial.println(y);
    last_x = x;
    last_y = y;
  }
  
  if(!digitalRead(IRQ_PIN)) {  // Uncomment to use IRQ */
    uint32_t buttons = ss.digitalReadBulk(button_mask);

    sendPacket(last_x,last_y,buttons);
//    Serial.println(buttons, BIN);

    if (! (buttons & (1 << BUTTON_RIGHT))) {
      Serial.println("Button A pressed");
    }
    if (! (buttons & (1 << BUTTON_DOWN))) {
      Serial.println("Button B pressed");
    }
    if (! (buttons & (1 << BUTTON_LEFT))) {
      Serial.println("Button Y pressed");
    }
    if (! (buttons & (1 << BUTTON_UP))) {
      Serial.println("Button X pressed");
    }
    if (! (buttons & (1 << BUTTON_SEL))) {
      Serial.println("Button SEL pressed");
    }
  } // Uncomment to use IRQ */
  delay(10);
}
