  #include <WiFi.h>
  #include <PubSubClient.h>
  #include <ArduinoJson.h>
  #include <M5StickCPlus2.h>
  #include <DFRobot_DHT11.h>
  #include "time.h"
  #include "ESP32TimerInterrupt.h"

  #define LED 26
  #define DATA 0
  #define ID 999
  #define NTP_TIMEZONE "UTC-8"
  #define NTP_SERVER1 "0.pool.ntp.org"
  #define NTP_SERVER2 "1.pool.ntp.org"
  #define NTP_SERVER3 "2.pool.ntp.org"
  //graph variable
  #define BUFFER_SIZE 120
  #define ACCEL_RANGE 2.0
  #define GYRO_RANGE 500.0
  #define GRAPH_HEIGHT 50
  #define TOP_MARGIN 70 


  #define TIMER0_INTERVAL_MS 9800 
  #define ALARM_STOP_DURATION 2000  // 2-second long press to stop alarm

  // Init ESP32 timer 0
  ESP32Timer ITimer0(0);

  bool flag = false;
  int count = 0;

  bool IRAM_ATTR TimerHandler0(void *timerNo) {
    flag = true;
    count++;
    return true;
  }

  // DHT11
  DFRobot_DHT11 dht;
  // MQTT and WiFi set-up
  WiFiClient espClient;
  PubSubClient client(espClient);

  // Menu system
  struct MenuItem {
    const char* name;
    void (*action)();
    struct Menu* childMenu;
  };

  struct Menu {
    const char* title;
    MenuItem* items;
    int itemCount;
    int selectedIndex;
    int topIndex;
    Menu* parentMenu;
  };

  // Function prototypes
  void drawMenu(Menu* menu);
  void navigateNext(Menu* menu);
  void selectItem(Menu* menu);
  void actionShowTempHum();
  void actionShowTime();
  void actionShowMotion();
  void actionToggleMQTT();
  void actionSoundAlarm();
  void actionAttendanceSystem();
  void actionBack();
  void drawAnalogClock(int hour, int minute, int second);
  void triggerAlarm();
  void updateAttendance();
  void mqttCallback(char* topic, byte* payload, unsigned int length);
  void stopAlarm();

  // Global states
  enum AppState { STATE_MENU, STATE_TEMP_HUM, STATE_TIME, STATE_MOTION, STATE_ATTENDANCE };
  AppState currentState = STATE_MENU;
  Menu* currentMenu = nullptr;

  // Clock variables
  const int CLOCK_CENTER_X = 70;
  const int CLOCK_CENTER_Y = 110;
  const int CLOCK_RADIUS = 30;
  unsigned long lastClockUpdate = 0;

  // Sensor data
  float accelX[BUFFER_SIZE] = {0};
  float accelY[BUFFER_SIZE] = {0};
  float accelZ[BUFFER_SIZE] = {0};
  float gyroX[BUFFER_SIZE] = {0};
  float gyroY[BUFFER_SIZE] = {0};
  float gyroZ[BUFFER_SIZE] = {0};
  int bufferIndex = 0;
  unsigned long lastUpdate = 0;

  float ax, ay, az;
  float gx, gy, gz;
  float temp, hum;
  char msg[200];
  String ipAddress;
  String macAddr;
  String recMsg="";
  // Alarm variables
  bool alarmActive = false;
  unsigned long alarmStartTime = 0;
  const unsigned long alarmDuration = 4800; // 5 seconds

  // Attendance system
  const char* students[] = {"Keung To", "Naruto", "Yasou", "BaBa", "IShowspeed"};
  const int numStudents = 5;
  bool attendance[numStudents] = {false};
  int attendanceIndex = 0;

  // MQTT Config
  const char *ssid = "EIA-W311MESH";
  const char *password = "42004200";
  const char *mqtt_server = "ia.ic.polyu.edu.hk";
  char *mqttTopic = "TeamC05Alarm";
  char *mattTopic = "IC/TeamC05";
  StaticJsonDocument<900> Jsondata;

  // Menu declarations
  MenuItem tempHumItem = { "Temp & Hum", actionShowTempHum, nullptr };
  MenuItem timeItem = { "Current Time", actionShowTime, nullptr };
  MenuItem motionItem = { "Motion Status", actionShowMotion, nullptr };
  MenuItem mqttItem = { "Toggle MQTT", actionToggleMQTT, nullptr };
  MenuItem alarmItem = { "Sound Alarm", actionSoundAlarm, nullptr };
  MenuItem attendanceItem = { "Attendance", actionAttendanceSystem, nullptr };

  MenuItem mainItems[] = { tempHumItem, timeItem, motionItem, mqttItem, alarmItem, attendanceItem };
  Menu mainMenu = {
    "Main Menu",
    mainItems,
    6, // Updated count
    0,
    0,
    nullptr
  };

  // Clock colors
  #define CLOCK_BG BLACK
  #define CLOCK_FACE DARKGREY
  #define HOUR_COLOR WHITE
  #define MINUTE_COLOR GREEN
  #define SECOND_COLOR RED
  #define MARKER_COLOR WHITE

  void actionShowTempHum() {
    currentState = STATE_TEMP_HUM;
  }

  void actionShowTime() {
    currentState = STATE_TIME;
  }

  void actionShowMotion() {
    currentState = STATE_MOTION;
  }

  void actionToggleMQTT() {
    if (Jsondata["Start"] == "False") {
      Jsondata["Start"] = "True";
    } else {
      Jsondata["Start"] = "False";
    }
    drawMenu(currentMenu);  // Refresh menu to show updated state
  }

  void actionSoundAlarm() {
    triggerAlarm();
  }

  void actionAttendanceSystem() {
    currentState = STATE_ATTENDANCE;
    attendanceIndex = 0; // Reset to first student
  }

  void actionBack() {
    M5.Lcd.setTextSize(2);
    currentState = STATE_MENU;
    drawMenu(currentMenu);
  }

  void setup_wifi() {
    byte count = 0;
    WiFi.disconnect();
    delay(100);
    M5.Lcd.setTextSize(1);
    Serial.printf("\nConnecting to %s\n", ssid);
    WiFi.begin(ssid, password);

    long currentTime = millis();
    M5.Lcd.setCursor(10, 10);
    M5.Lcd.print("Connecting");
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
      M5.Lcd.print(".");
      count++;
      
      if (count == 6) {
        count = 0;
        M5.Lcd.fillRect(10, 10, 150, 20, BLACK);
        M5.Lcd.setCursor(10, 10);
      }
        
      if (millis()-currentTime > 30000) ESP.restart();
    }
    
    ipAddress = WiFi.localIP().toString();
    macAddr = WiFi.macAddress();
    
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setCursor(10, 10);
    M5.Lcd.print("WiFi connected!");
    delay(2000);
  }

  void reconnect() {
    while (!client.connected()) {
      Serial.printf("Attempting MQTT connection...");
      if (client.connect(macAddr.c_str())) {
        Serial.println("Connected");
        snprintf(msg, 75, "IoT System (%s) READY", ipAddress.c_str());
        client.subscribe(mqttTopic);
        delay(1000);
        client.publish(mqttTopic, msg);
      } else {
        Serial.print("failed, rc=");
        Serial.print(client.state());
        Serial.println(" try again in 5 seconds");
        delay(5000);
      }
    }
  }

  void check_Accel() {
    if (temp == 255){
      temp = 25;
    }
    if (hum == 255){
      hum = 60;
    }
    Jsondata["Temp"] = temp;
    Jsondata["Hum"] = hum;

    if ((abs(ax) > 0.2) || (abs(ay) > 0.2) || (abs(az-1) > 0.2)) {
      if (flag == true) {
        Jsondata["MOVED"] = "Yes";
        serializeJson(Jsondata, msg);
        if (Jsondata["Start"] == "True") {
          client.publish(mattTopic, msg);
          }
        
        else {
          client.publish(mattTopic, msg);
          Jsondata["MOVED"] = "No";
          };
      flag = false;
    }
  }
    if ((abs(ax) > 40) || (abs(ay) > 20) || (abs(az-1) > 20)) {
      Jsondata["MOVED"] = "Move fastly";
      serializeJson(Jsondata, msg);
      if (Jsondata["Start"] == "True") client.publish(mattTopic, msg);
    }
}

  void drawMenu(Menu* menu) {
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setCursor(5, 10);
    M5.Lcd.setTextSize(2);
    M5.Lcd.printf("%s", menu->title);
    M5.Lcd.drawFastHLine(5, 35, 150, WHITE);
    StickCP2.Display.fillCircle(25,200,20,255);
    StickCP2.Display.fillCircle(65,200,20,GREEN);
    StickCP2.Display.fillCircle(105,200,20,RED);
    
    
    // Adjust text size to fit more items
    M5.Lcd.setTextSize(1);
    
    int maxVisible = min(6, menu->itemCount - menu->topIndex);
    for (int i = 0; i < maxVisible; i++) {
      int itemIndex = menu->topIndex + i;
      int yPos = 45 + i * 20;  // Reduced spacing between items
      
      if (itemIndex == menu->selectedIndex) {
        M5.Lcd.setTextColor(BLACK, WHITE);
        M5.Lcd.fillRect(3, yPos - 3, 150, 18, WHITE);  // Smaller highlight box
      } else {
        M5.Lcd.setTextColor(WHITE, BLACK);
      }
      
      M5.Lcd.setCursor(5, yPos);
      
      // Special case for MQTT toggle
      if (strcmp(menu->items[itemIndex].name, "Toggle MQTT") == 0) {
        M5.Lcd.printf("%s: %s", 
          menu->items[itemIndex].name, 
          Jsondata["Start"].as<const char*>());
      } else {
        M5.Lcd.print(menu->items[itemIndex].name);
      }
    }
  }

  void navigateNext(Menu* menu) {
    menu->selectedIndex = (menu->selectedIndex + 1) % menu->itemCount;
    
    // Adjust scrolling to show all 6 items
    if (menu->selectedIndex >= menu->topIndex + 6) {
      menu->topIndex++;
    } else if (menu->selectedIndex < menu->topIndex) {
      menu->topIndex = menu->selectedIndex;
    }
  }

  void selectItem(Menu* menu) {
    MenuItem* item = &menu->items[menu->selectedIndex];
    if (item->action) item->action();
  }

  void drawTempHum() {
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setCursor(10, 20);
    M5.Lcd.printf("Temperature: %.1fC", temp);
    M5.Lcd.setCursor(10, 60);
    M5.Lcd.printf("Humidity: %.1f%%", hum);
    M5.Lcd.setCursor(10, 100);
    //M5.Lcd.printf("MQTT: %s", Jsondata["Start"].as<const char*>());
    M5.Lcd.setCursor(10, 140);
    M5.Lcd.print("Press A to back");
    delay(800);
  }

  // Draw analog clock
  void drawAnalogClock(int hour, int minute, int second) {
    // Draw clock face
    M5.Lcd.fillCircle(CLOCK_CENTER_X, CLOCK_CENTER_Y, CLOCK_RADIUS, CLOCK_FACE);
    M5.Lcd.fillCircle(CLOCK_CENTER_X, CLOCK_CENTER_Y, CLOCK_RADIUS-2, CLOCK_BG);
    
    // Draw hour markers
    for (int i = 0; i < 12; i++) {
      float angle = i * 30 * PI / 180;
      int x1 = CLOCK_CENTER_X + (CLOCK_RADIUS-5) * cos(angle);
      int y1 = CLOCK_CENTER_Y + (CLOCK_RADIUS-5) * sin(angle);
      int x2 = CLOCK_CENTER_X + (CLOCK_RADIUS-2) * cos(angle);
      int y2 = CLOCK_CENTER_Y + (CLOCK_RADIUS-2) * sin(angle);
      M5.Lcd.drawLine(x1, y1, x2, y2, MARKER_COLOR);
    }
    
    // Draw hour hand
    float hourAngle = (hour % 12 + minute / 60.0) * 30 * PI / 180;
    int hx = CLOCK_CENTER_X + (CLOCK_RADIUS * 0.5) * cos(hourAngle - PI/2);
    int hy = CLOCK_CENTER_Y + (CLOCK_RADIUS * 0.5) * sin(hourAngle - PI/2);
    M5.Lcd.drawLine(CLOCK_CENTER_X, CLOCK_CENTER_Y, hx, hy, HOUR_COLOR);
    
    // Draw minute hand
    float minuteAngle = (minute + second / 60.0) * 6 * PI / 180;
    int mx = CLOCK_CENTER_X + (CLOCK_RADIUS * 0.7) * cos(minuteAngle - PI/2);
    int my = CLOCK_CENTER_Y + (CLOCK_RADIUS * 0.7) * sin(minuteAngle - PI/2);
    M5.Lcd.drawLine(CLOCK_CENTER_X, CLOCK_CENTER_Y, mx, my, MINUTE_COLOR);
    
    // Draw second hand
    float secondAngle = second * 6 * PI / 180;
    int sx = CLOCK_CENTER_X + (CLOCK_RADIUS * 0.8) * cos(secondAngle - PI/2);
    int sy = CLOCK_CENTER_Y + (CLOCK_RADIUS * 0.8) * sin(secondAngle - PI/2);
    M5.Lcd.drawLine(CLOCK_CENTER_X, CLOCK_CENTER_Y, sx, sy, SECOND_COLOR);
    
    // Draw center cap
    M5.Lcd.fillCircle(CLOCK_CENTER_X, CLOCK_CENTER_Y, 3, WHITE);
  }

  void drawTime() {
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
      M5.Lcd.fillScreen(BLACK);
      M5.Lcd.setCursor(10, 10);
      M5.Lcd.print("Failed to get time");
      return;
    }
    
    M5.Lcd.fillScreen(BLACK);
    
    // Draw digital time at top
    M5.Lcd.setCursor(10, 10);
    M5.Lcd.printf("Time: %02d:%02d:%02d", 
      timeinfo.tm_hour, 
      timeinfo.tm_min, 
      timeinfo.tm_sec);
    
    // Draw date below time
    M5.Lcd.setCursor(10, 40);
    M5.Lcd.printf("Date: %04d/%02d/%02d", 
      timeinfo.tm_year + 1900, 
      timeinfo.tm_mon + 1, 
      timeinfo.tm_mday);
    
    // Draw analog clock
    drawAnalogClock(timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
    
    // Draw MQTT status at bottom
    M5.Lcd.setCursor(10, 170);
    //M5.Lcd.printf("MQTT: %s", Jsondata["Start"].as<const char*>());
    
    // Draw return instruction
    M5.Lcd.setCursor(10, 200);
    M5.Lcd.print("Press A to back");
    delay(800);
  }

  void drawMotion() {
    M5.Lcd.setTextSize(1);
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setCursor(5, 10);
    M5.Lcd.printf("Accel:%.2f,%.2f,%.2f", ax, ay, az);
    M5.Lcd.setCursor(5, 20);
    M5.Lcd.printf("Gyro:%.2f,%.2f,%.2f", gx, gy, gz);
    M5.Lcd.setCursor(5, 40);
    M5.Lcd.printf("Movement:%s", Jsondata["MOVED"].as<const char*>());
    M5.Lcd.setCursor(5, 190);
    M5.Lcd.print("Press A to back");

    if (millis() - lastUpdate >= 50) {
      lastUpdate = millis();
      
      // Read sensor data
      float ax, ay, az, gx, gy, gz;
      StickCP2.Imu.getAccelData(&ax, &ay, &az);
      StickCP2.Imu.getGyroData(&gx, &gy, &gz);
      
      // Store in buffers
      accelX[bufferIndex] = ax;
      accelY[bufferIndex] = ay;
      accelZ[bufferIndex] = az;
      gyroX[bufferIndex] = gx;
      gyroY[bufferIndex] = gy;
      gyroZ[bufferIndex] = gz;
      
      // Update graphs
      updateGraphs();
      
      // Move to next buffer position
      bufferIndex = (bufferIndex + 1) % BUFFER_SIZE;
      }
    
    
  
}
  // 1. Alarm function
  void triggerAlarm() {
    if (!alarmActive) {
      alarmActive = true;
      alarmStartTime = millis();
      //5.Speaker.setVolume(270);
      //M5.Speaker.tone(0, 0); // Start the alarm tone
    }
  }

  void stopAlarm() {
    alarmActive = false;
    digitalWrite(LED, LOW);
    M5.Speaker.tone(0, 0);
  }

  // 2. Draw attendance system
  void drawAttendance() {
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setCursor(10, 10);
    M5.Lcd.print("Attendance System");
    M5.Lcd.drawFastHLine(5, 35, 150, WHITE);
    
    // Display students
    for (int i = 0; i < numStudents; i++) {
      int yPos = 50 + i * 20;  // Reduced spacing
      
      if (i == attendanceIndex) {
        M5.Lcd.setTextColor(BLACK, WHITE);
        M5.Lcd.fillRect(3, yPos - 3, 150, 18, WHITE);  // Smaller highlight
      } else {
        M5.Lcd.setTextColor(WHITE, BLACK);
      }
      
      M5.Lcd.setCursor(5, yPos);
      M5.Lcd.printf("%s: %s", students[i], attendance[i] ? "Present" : "Absent");
      Jsondata[students[i]] = attendance[i];
    }
    
    // Instructions
    M5.Lcd.setTextColor(WHITE, BLACK);
    M5.Lcd.setCursor(5, 180);
    M5.Lcd.print("HoldA:Tick attendance  B:Next  ");
  }

  // 3. MQTT callback for incoming messages
  void mqttCallback(char* topic, byte* payload, unsigned int length) {
    // Convert payload to string
    char message[length+1];
    memcpy(message, payload, length);
    message[length] = '\0';
    
    Serial.print("Message arrived: ");
    Serial.println(message);
    
    // Check for "help" message
    if (strcmp(message, "Alarm:True") == 0) {
      triggerAlarm();
    }
  }

  void updateGraphs() {
    // Update accelerometer graph (top graph section)
    for (int x = 0; x < BUFFER_SIZE - 1; x++) {
      int idx0 = (bufferIndex + x) % BUFFER_SIZE;
      int idx1 = (bufferIndex + x + 1) % BUFFER_SIZE;
      
      // Clear previous vertical line in top graph area
      M5.Lcd.drawFastVLine(x, TOP_MARGIN, GRAPH_HEIGHT, BLACK);
      
      // Draw new data points in top graph area
      drawGraphLine(x, accelX[idx0], accelX[idx1], ACCEL_RANGE, TOP_MARGIN, RED);
      drawGraphLine(x, accelY[idx0], accelY[idx1], ACCEL_RANGE, TOP_MARGIN, GREEN);
      drawGraphLine(x, accelZ[idx0], accelZ[idx1], ACCEL_RANGE, TOP_MARGIN, BLUE);
    }
    
    // Update gyroscope graph (bottom graph section)
    for (int x = 0; x < BUFFER_SIZE - 1; x++) {
      int idx0 = (bufferIndex + x) % BUFFER_SIZE;
      int idx1 = (bufferIndex + x + 1) % BUFFER_SIZE;
      
      // Clear previous vertical line in bottom graph area
      M5.Lcd.drawFastVLine(x, TOP_MARGIN + GRAPH_HEIGHT + 1, GRAPH_HEIGHT, BLACK);
      
      // Draw new data points in bottom graph area
      drawGraphLine(x, gyroX[idx0], gyroX[idx1], GYRO_RANGE, TOP_MARGIN + GRAPH_HEIGHT + 1, RED);
      drawGraphLine(x, gyroY[idx0], gyroY[idx1], GYRO_RANGE, TOP_MARGIN + GRAPH_HEIGHT + 1, GREEN);
      drawGraphLine(x, gyroZ[idx0], gyroZ[idx1], GYRO_RANGE, TOP_MARGIN + GRAPH_HEIGHT + 1, BLUE);
    }
  }

  void drawGraphLine(int x, float val0, float val1, float range, int yOffset, uint16_t color) {
    // Map sensor values to screen coordinates
    int y0 = map(val0 * 1000, -range * 1000, range * 1000, GRAPH_HEIGHT - 1, 0) + yOffset;
    int y1 = map(val1 * 1000, -range * 1000, range * 1000, GRAPH_HEIGHT - 1, 0) + yOffset;
    
    // Constrain to graph area
    y0 = constrain(y0, yOffset, yOffset + GRAPH_HEIGHT - 1);
    y1 = constrain(y1, yOffset, yOffset + GRAPH_HEIGHT - 1);
    
    // Draw line segment
    M5.Lcd.drawLine(x, y0, x + 1, y1, color);
  }

  void setup() {
    Serial.begin(115200);
    M5.begin();
    M5.Imu.init();
    M5.Lcd.setRotation(0);  // Portrait orientation
    M5.Lcd.setTextSize(2);  // All text size 2
    M5.Lcd.setTextColor(WHITE, BLACK);
    pinMode(LED, OUTPUT);
    digitalWrite(LED, LOW);
    setup_wifi();
    client.setServer(mqtt_server, 1883);
    client.setCallback(mqttCallback); // Set MQTT callback
    
    // Initialize JSON
    Jsondata["PART"] = ID;
    Jsondata["MOVED"] = "No";
    Jsondata["Start"] = "FALSE";
    
    configTzTime(NTP_TIMEZONE, NTP_SERVER1, NTP_SERVER2, NTP_SERVER3);
    
    // Initialize menu
    currentMenu = &mainMenu;
    drawMenu(currentMenu);
    
    // Start the timer
    if (ITimer0.attachInterruptInterval(TIMER0_INTERVAL_MS * 1000, TimerHandler0)) {
      Serial.print(F("Starting ITimer0 OK, millis() = "));
      Serial.println(millis());
    } else {
      Serial.println(F("Can't set ITimer0. Select another freq. or timer"));
    }
  }

  void loop() {
    M5.update();
    
    // Handle alarm
    if (alarmActive) {
      // Continue playing the alarm tone
      //digitalWrite(LED,digitalRead(LED)^1);
      //M5.Speaker.tone(9000,4000);
    digitalWrite(LED, !digitalRead(LED));  // Toggle LED
    M5.Speaker.tone(9000, 200,-1);
      // Check for stop conditions
      if (M5.BtnA.pressedFor(ALARM_STOP_DURATION)) {
        stopAlarm();
      }
      // Auto-stop after duration
      else if (millis() - alarmStartTime >= alarmDuration) {
        stopAlarm();
        
      }
    }
    
    // Read sensors
    dht.read(DATA);
    hum = dht.humidity;  
    temp = dht.temperature;
    
    if (M5.Imu.update()) {
      auto data = M5.Imu.getImuData();
      ax = data.accel.x;
      ay = data.accel.y;  
      az = data.accel.z;
      gx = data.gyro.x;
      gy = data.gyro.y;
      gz = data.gyro.z;
      
      check_Accel();
    }
    
    // Handle MQTT
    if (!client.connected()) reconnect();
    client.loop();

    // Handle display states
    if (M5.BtnA.wasPressed()) {
      if (currentState == STATE_MENU) {
        selectItem(currentMenu);
      } else if (currentState == STATE_ATTENDANCE) {
        // Mark attendance for selected student
        attendance[attendanceIndex] = !attendance[attendanceIndex];
      } else {
        actionBack();
      }
    }
    
    if (M5.BtnB.wasPressed() && currentState == STATE_MENU) {
      navigateNext(currentMenu);
      drawMenu(currentMenu);
    } else if (M5.BtnB.wasPressed() && currentState == STATE_ATTENDANCE) {
      // Next student
      attendanceIndex = (attendanceIndex + 1) % numStudents;
    }
    
    if (M5.BtnA.pressedFor(1000) && currentState == STATE_ATTENDANCE) {
      // Long press to go back
      actionBack();
    }
    
    // Update displays
    switch (currentState) {
      case STATE_MENU:
        // Menu is drawn by button handlers
        break;
      case STATE_TEMP_HUM:
        drawTempHum();
        break;
      case STATE_TIME:
        drawTime();
        break;
      case STATE_MOTION:
        drawMotion();
        break;
      case STATE_ATTENDANCE:
        drawAttendance();
        break;
    }
    
    // Update clock every second in time view
    if (currentState == STATE_TIME && millis() - lastClockUpdate >= 1000) {
      struct tm timeinfo;
      if (getLocalTime(&timeinfo)) {
        M5.Lcd.fillRect(0, 70, 160, 80, BLACK); // Clear clock area
        drawAnalogClock(timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
        lastClockUpdate = millis();
      }
    }
    
  }