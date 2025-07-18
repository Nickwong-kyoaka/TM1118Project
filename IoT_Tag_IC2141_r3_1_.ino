/*****************************************************************************
Smart IOT Tag to show staff's status
Using ESP8266

This sketch connects the ESP8266 to a MQTT broker and subscribes to the topic 
/IC/TRIAL. When the button is pressed, the client will toggle among publishing
"Available", "Busy", "Online" and "Leave". When the Json message is received, 
the LED matrix displays "A", "B", "O" and "L", respectively. 

R1: 1st release
R2: Correct client.subscribe inside reconnect()
*******************************************************************************/

#include <SPI.h>
#include <ButtonDebounce.h>     // Button Debounce library
#include <ESP8266WiFi.h>        // 8266 Wifi driver
#include <PubSubClient.h>       // MQTT server library
#include <ArduinoJson.h>        // JSON library
#include "LedMatrix.h"          // LED control library

#define NUMBER_OF_DEVICES 1
#define CS_PIN D4

#define red_light_pin D0    // red light is connected to D0
#define green_light_pin D8  // green light is connected to D8
#define blue_light_pin D3   // blue light is connected to D3
#define TRIG D2             // swith is connected to D2
#define ID 5

LedMatrix ledMatrix = LedMatrix(NUMBER_OF_DEVICES, CS_PIN);

// MQTT and WiFi set-up
WiFiClient espClient;
PubSubClient client(espClient); // Open an MQTT client

// Key debounce set-up
ButtonDebounce trigger(TRIG, 100);

// The followings are NOT constants but strings with variable length
const char *ssid = "EIA-W311MESH";              // Your SSID             
const char *password = "42004200";              // Your Wifi password
//const char *ssid = "icw502g";                 // Your SSID             
//const char *password = "8c122ase";           // Your Wifi password
//const char *ssid = "TM0512";                 // Your SSID             
//const char *password = "05120512";           // Your Wifi password
const char *mqtt_server = "ia.ic.polyu.edu.hk"; // MQTT server name
//const char *mqtt_server = "192.168.0.170"; // MQTT server name
const char *mqttTopic_TX = "IC/C05";            // Topic to subscribe to  
const char *mqttTopic_RX = "IC/TM1118/TEAM_A/SUB";            // Topic to subscribe to    

byte reconnect_count = 0;
int count = 0;
long int currentTime = 0;

char msg[200];
String ipAddress;
String macAddr;
String recMsg="";

int buttonState;      // variable to hold the button state
int Mode = 0;         // what mode is the light in?
boolean keypress = 1;

// The followings are NOT constants but strings with variable length
const char *Team="C06";   
const char *value="Available";

StaticJsonDocument<50> Jsondata; // Create a JSON document of 200 characters max
StaticJsonDocument<100> jsonBuffer; 


//Set up the Wifi connection
void setup_wifi() {
  WiFi.disconnect();
  delay(100);
  // We start by connecting to a WiFi network
  Serial.printf("\nConnecting to %s\n", ssid);
  WiFi.begin(ssid, password); // start the Wifi connection with defined SSID and PW

  // Indicate "......" during connecting and flashing LED1
  // Restart if WiFi cannot be connected for 30sec
  currentTime = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(green_light_pin,digitalRead(green_light_pin)^1);
    if (millis()-currentTime > 30000){
      ESP.restart();
    }
  }
  // Show "WiFi connected" once linked and light up LED1
  Serial.printf("\nWiFi connected\n");
  digitalWrite(green_light_pin,LOW);
  delay(2000);
  digitalWrite(green_light_pin,HIGH);
  
  // Show IP address and MAC address
  ipAddress=WiFi.localIP().toString();
  Serial.printf("\nIP address: %s\n", ipAddress.c_str());
  macAddr=WiFi.macAddress();
  Serial.printf("MAC address: %s\n", macAddr.c_str());
}

// Routine to receive message from MQTT server
void callback(char* topic, byte* payload, unsigned int length) {
  
  recMsg ="";
  for (int i = 0; i < length; i++) {
    recMsg = recMsg + (char)payload[i];
  }
  
  DeserializationError error = deserializeJson(jsonBuffer, recMsg);

  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.c_str());
    return;
  }

  Team = jsonBuffer["Name"];
  value = jsonBuffer["Status"];

  Serial.print(Team);
  Serial.println(value);


  //Check the curtain and value#
  if ((strcmp(Team, "C06") == 0) ) {
     if ((strcmp(value,"Available")==0)){
        ledMatrix.setText("A");
        digitalWrite(green_light_pin, LOW); // Green
        digitalWrite(red_light_pin, HIGH);
        digitalWrite(blue_light_pin, HIGH);
      }
     else if ((strcmp(value,"Busy")==0)){
        ledMatrix.setText("B");
        digitalWrite(green_light_pin, HIGH);
        digitalWrite(red_light_pin, LOW); //Red
        digitalWrite(blue_light_pin, HIGH);
      }
     else if ((strcmp(value,"Online")==0)){
        ledMatrix.setText("O");
        digitalWrite(green_light_pin, LOW); //Amber
        digitalWrite(red_light_pin, LOW); //Amber
        digitalWrite(blue_light_pin, HIGH);
      }
     else if ((strcmp(value,"Leave")==0)){
        ledMatrix.setText("L");
        digitalWrite(green_light_pin, HIGH);
        digitalWrite(red_light_pin, HIGH); 
        digitalWrite(blue_light_pin, LOW); //Blue
      }
       ledMatrix.clear();
       ledMatrix.drawText();
       ledMatrix.commit();
       delay(200);
  }


  //Clear the buffer
  jsonBuffer.clear();  
  delay(100);
}


// Reconnect mechanism for MQTT Server
void reconnect() {
  
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.printf("Attempting MQTT connection...");
    // Attempt to connect
    //if (client.connect("ESP32Client")) {
    if (client.connect(macAddr.c_str())) {
      Serial.println("Connected");
      // Once connected, publish an announcement...
      // Also subscribe to the topic but not ready to receive yet
      snprintf(msg, 75, "IoT System (%s) is READY", ipAddress.c_str());
      Serial.println(msg);
      client.subscribe(mqttTopic_RX); // Subscribe to the topic
      client.publish(mqttTopic_TX, msg);
      reconnect_count = 0;
    } 
    else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      reconnect_count++;
      
      //Reconnect wifi by restart if retrial up to 5 times
      if (reconnect_count == 5){
        ESP.restart(); // Reset if not connected to server 
      }
        
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

// Button control
void buttonChanged(int state){
  if (digitalRead(TRIG)== 0 && keypress==1) {  // If key is pressed and last key is processed
    Mode++;
    if (Mode == 5) Mode=0;      // Reset Mode value
    keypress=0;
  }
}


void setup() {
  pinMode(TRIG, INPUT_PULLUP);          // Configure TRIG as an pull-up input
  pinMode(red_light_pin, OUTPUT);
  pinMode(green_light_pin, OUTPUT);
  pinMode(blue_light_pin, OUTPUT);
  
  digitalWrite(red_light_pin, HIGH);
  digitalWrite(green_light_pin, HIGH);
  digitalWrite(blue_light_pin, HIGH);

  buttonState = digitalRead(TRIG);      // Read the initial state
  
  Serial.begin(115200);                 // State serial communication at 115200 baud
  Serial.println("System Start!");

  //Initiate the display first
  ledMatrix.init();                             // Initialize the SPI interface
  ledMatrix.setIntensity(4);                    // Light intensity: 0 - 15
  ledMatrix.setTextAlignment(TEXT_ALIGN_LEFT);  // Text is aligned to left side of the display

  //Initial state is available
  digitalWrite(green_light_pin, LOW); // Green
  digitalWrite(red_light_pin, HIGH);
  digitalWrite(blue_light_pin, HIGH);
  ledMatrix.setText("T");
  ledMatrix.clear();
  ledMatrix.drawText();
  ledMatrix.commit();
  
  client.setCallback(callback);
  trigger.setCallback(buttonChanged);

  setup_wifi(); // Connect to network
  digitalWrite(green_light_pin, LOW); // Green
  client.setServer(mqtt_server, 1883);
    
  //Initalize Json message
  Jsondata["Name"] = "C06";
  Jsondata["Status"] = "Available";  
}

void loop() {
  trigger.update(); //key scanning
  if (!client.connected()){  // Reconnect if connection is lost
    reconnect();
  }
  client.loop(); //Listen to the topic
  // Now do whatever the lightMode indicates

  if (keypress ==0) {
      if (Mode == 0) {// Available
        digitalWrite(green_light_pin, LOW); // Green
        digitalWrite(red_light_pin, HIGH);
        digitalWrite(blue_light_pin, HIGH);
        ledMatrix.setText("T");
        ledMatrix.clear();
        ledMatrix.drawText();
        ledMatrix.commit();
        
        Jsondata["Stage"] = "Time";
        // Packing the JSON message into msg
        serializeJson(Jsondata, Serial);
        serializeJson(Jsondata, msg); 
        
        //Publish msg to MQTT server
        client.publish(mqttTopic_TX, msg);
        Serial.println();
        keypress=1;
        delay(2000);
      }

      if (Mode == 1) {// Busy
        digitalWrite(red_light_pin, LOW); // Red
        digitalWrite(green_light_pin, HIGH);
        digitalWrite(blue_light_pin, HIGH);
        ledMatrix.setText("D");
        ledMatrix.clear();
        ledMatrix.drawText();
        ledMatrix.commit();
        
        Jsondata["Stage"] = "Data";
        // Packing the JSON message into msg
        serializeJson(Jsondata, Serial);
        serializeJson(Jsondata, msg); 
        
        //Publish msg to MQTT server
        client.publish(mqttTopic_TX, msg);
        Serial.println();
        keypress=1;
        delay(2000);
      }

      if (Mode == 2) {// Online
        // Amber(Green + Red)
        digitalWrite(green_light_pin, LOW); 
        digitalWrite(red_light_pin, LOW);
        digitalWrite(blue_light_pin, HIGH);
        ledMatrix.setText("S");
        ledMatrix.clear();
        ledMatrix.drawText();
        ledMatrix.commit();
        
        Jsondata["Stage"] = "Stopwatch";
        // Packing the JSON message into msg
        serializeJson(Jsondata, Serial);
        serializeJson(Jsondata, msg); 
        
        //Publish msg to MQTT server
        client.publish(mqttTopic_TX, msg);
        Serial.println();
        keypress=1;
        delay(2000);
      }
      
      if (Mode == 3) { // Leave
        digitalWrite(blue_light_pin, LOW); // Blue
        digitalWrite(red_light_pin, HIGH);
        digitalWrite(green_light_pin, HIGH);
        ledMatrix.setText("M");
        ledMatrix.clear();
        ledMatrix.drawText();
        ledMatrix.commit();        
        
        Jsondata["Stage"] = "Music";
        
        // Packing the JSON message into msg
        serializeJson(Jsondata, Serial);
        serializeJson(Jsondata, msg); 
        
        //Publish msg to MQTT server
        client.publish(mqttTopic_TX, msg);
        Serial.println();
        keypress=1;
        delay(2000);
      }
      if (Mode == 4) {
        digitalWrite(blue_light_pin, HIGH); // Blue
        digitalWrite(red_light_pin, LOW);
        digitalWrite(green_light_pin, HIGH);
        ledMatrix.setText("D");
        ledMatrix.clear();
        ledMatrix.drawText();
        ledMatrix.commit();
        Jsondata["Stage"] = "Alarm";
        serializeJson(Jsondata, Serial);
        serializeJson(Jsondata, msg); 
        
        //Publish msg to MQTT server
        client.publish(mqttTopic_TX, msg);
        Serial.println();
        keypress=1;
        delay(2000);
      }
  
  }
}
