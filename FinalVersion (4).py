import signal
import sys
import time
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
import Adafruit_ADS1x15
import math
import Adafruit_DHT
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import pytz

def bigtime():
    if mode != "Time":
        button_callback(21)
    lcd.clear()
    global should_blink, should_open
    clock_active = True
    last_second = None
    
    toptop = (
        0b11111,
        0b11111,
        0b11111,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000
    )
    lefttop = (
        0b00111,
        0b01111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111       
    )
    middletop =(
        0b11111,
        0b11111,
        0b11111,
        0b00000,
        0b00000,
        0b00000,
        0b11111,
        0b11111  
    )
    righttop = (
        0b11100,
        0b11110,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111       
    )
    leftdown = (
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b01111,
        0b00111       
    )
    middledown =(
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b11111,
        0b11111,
        0b11111  
    )
    rightdown = (
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11110,
        0b11100       
    )
    
    name = [lefttop, middletop, righttop, leftdown, middledown, rightdown, toptop]
    for i in range(7):
        lcd.create_char(i, name[i])
    
    while clock_active:
        if not GPIO.input(21):  
            clock_active = False
            lcd.clear()
            break
        now = time.localtime()
        current_second = now.tm_sec
        if current_second != last_second:
            last_second = current_second
            nowhour = time.strftime("%H", now)
            nowmin = time.strftime("%M", now)
            nowsec = time.strftime("%S", now)
            
            lcd.cursor_pos = (0, 0)
            lcd.write_string("                ")  
            lcd.cursor_pos = (1, 0)
            lcd.write_string("                ")  
            lcd.cursor_pos = (1, 14)
            lcd.write_string(nowsec)
        
            for ppt, char in enumerate(nowhour):
                if ppt == 1:
                    ppt = ppt + 2
                if char == "0":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x03')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x06')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+2); lcd.write_string('\x02')
                    lcd.cursor_pos = (1, ppt+2); lcd.write_string('\x05')
                elif char == "1":
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x00')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x03')
                elif char == "2":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x06')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x02')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x03')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x04')
                elif char == "3":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x01')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x02')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x05')
                elif char == "4":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+2); lcd.write_string('\x02')
                    lcd.cursor_pos = (1, ppt+2); lcd.write_string('\x05')
                elif char == "5":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x01')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+2); lcd.write_string('\x06')
                    lcd.cursor_pos = (1, ppt+2); lcd.write_string('\x05')
                elif char == "6":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x03')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x01')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+2); lcd.write_string('\x06')
                    lcd.cursor_pos = (1, ppt+2); lcd.write_string('\x05')
                elif char == "7":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x06')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x03')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x05')
                elif char == "8":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x03')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x01')
            
                elif char == "9":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x01')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+2); lcd.write_string('\x02')
                    lcd.cursor_pos = (1, ppt+2); lcd.write_string('\x05')

        
            for ppt, char in enumerate(nowmin):
                if ppt == 0:
                    ppt = 7
                if ppt == 1:
                    ppt = 10
                
                if char == "0":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x03')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x06')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+2); lcd.write_string('\x02')
                    lcd.cursor_pos = (1, ppt+2); lcd.write_string('\x05')
            
                elif char == "1":
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x00')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x03')
                elif char == "2":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x06')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x02')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x03')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x04')
                elif char == "3":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x01')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x02')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x05')
                elif char == "4":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+2); lcd.write_string('\x02')
                    lcd.cursor_pos = (1, ppt+2); lcd.write_string('\x05')
                elif char == "5":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x01')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+2); lcd.write_string('\x06')
                    lcd.cursor_pos = (1, ppt+2); lcd.write_string('\x05')
                elif char == "6":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x03')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x01')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+2); lcd.write_string('\x06')
                    lcd.cursor_pos = (1, ppt+2); lcd.write_string('\x05')
                elif char == "7":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x06')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x03')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x05')
                elif char == "8":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (1, ppt); lcd.write_string('\x03')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x01')
            
                elif char == "9":
                    lcd.cursor_pos = (0, ppt); lcd.write_string('\x00')
                    lcd.cursor_pos = (0, ppt+1); lcd.write_string('\x01')
                    lcd.cursor_pos = (1, ppt+1); lcd.write_string('\x04')
                    lcd.cursor_pos = (0, ppt+2); lcd.write_string('\x02')
                    lcd.cursor_pos = (1, ppt+2); lcd.write_string('\x05')
            if int(nowsec) % 2 == 0:
                lcd.cursor_pos = (0, 6)
                lcd.write_string(".")
                lcd.cursor_pos = (1, 6)
                lcd.write_string(".")
                lcd.cursor_pos = (1, 13)
                lcd.write_string(":")
            if int(nowsec) % 4 == 0:
                lcd.cursor_pos = (0, 13); lcd.write_string("\x07")
            else:
                lcd.cursor_pos = (0, 15); lcd.write_string("\x07")
        
        time.sleep(0.1)
        
    
def button_callback(channel):
    
    print(" button enter")
    global mode, current_mode
    if get_dict["Stage"] :
        mode = get_dict["Stage"]
    if mode == "Time":
        lcd.clear()
        bigtime()
    if mode == "Stopwatch":
        lcd.clear()
        watch()
    if mode == "Music":
        lcd.clear()
        play_love_story()
    if mode == "Alarm":
        lcd.clear()
        alarm()
   
    if mode == "Data":
        lcd.clear()
        print("Data enter")
        if current_mode == "Part":
            print("part enter")
            lcd.clear()
            lcd.cursor_pos = (1, 0)
            lcd.write_string('\x00')
            lcd.cursor_pos = (1, 15)
            lcd.write_string('\x01')
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Part:")
            lcd.cursor_pos = (0, 7)
            lcd.write_string(str(receive_dict.get("PART", "N/A")))  
            current_mode="Moved"
        elif current_mode == "Moved":
            print("move enter")
            lcd.clear()
            lcd.cursor_pos = (1, 0)
            lcd.write_string('\x01')
            lcd.cursor_pos = (1, 15)
            lcd.write_string('\x00')
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Moved:")
            lcd.cursor_pos = (0, 10)
            lcd.write_string(str(receive_dict.get("MOVED", "N/A")))
            current_mode="Temp"

            
        elif current_mode == "Temp":
            print("Temp enter")
            lcd.clear()
            lcd.cursor_pos = (1, 0)
            lcd.write_string('\x00')
            lcd.cursor_pos = (1, 15)
            lcd.write_string('\x01')
            lcd.cursor_pos=(0,0)
            lcd.write_string("Temp:")
            lcd.cursor_pos=(0,7)
            lcd.write_string(str(receive_dict.get("Temp", "N/A")))
            current_mode ="Hum" 
            print(" updated")
            print(f"Received message on topic {msg.topic} : {d_msg}")
             
        elif current_mode == "Hum":
            lcd.clear()
            lcd.cursor_pos = (1, 0)
            lcd.write_string('\x01')
            lcd.cursor_pos = (1, 15)
            lcd.write_string('\x00')
            lcd.cursor_pos=(0,0)
            lcd.write_string("Hum:")
            lcd.cursor_pos=(0,7)
            lcd.write_string(str(receive_dict.get("Hum", "N/A")))
            current_mode ="Start"
            print(" updated")
            print(f"Received message on topic {msg.topic} : {d_msg}")
        elif current_mode == "Start":
            lcd.clear()
            lcd.cursor_pos = (1, 0)
            lcd.write_string('\x00')
            lcd.cursor_pos = (1, 15)
            lcd.write_string('\x01')
            lcd.cursor_pos=(0,0)
            lcd.write_string("Start:")
            lcd.cursor_pos=(0,7)
            lcd.write_string(str(receive_dict.get("Start", "N/A")))
            current_mode ="Part"
            print(" updated")
            print(f"Received message on topic {msg.topic} : {d_msg}")
        



def play_love_story():
    global mode
    while mode == "Music":

                
            
        lyrics = [
            (0, "Taylor Swift"),
            (2, "Love Story"),
            (5, "We were both     young"),
            (8, "when I first saw you"),
            (11, "I close my eyes"),
            (14, "and the         flashback starts"),
            (17, "I'm standing there"),
            (20, "on a balcony"),
            (23, "in summer air"),
            (27, "See the lights..."),
            (31, "see the party..."),
            (35, "the ball gowns..."),
            (39, "See you make your way"),
            (42, "through the crowd"),
            (45, "and say hello"),
            (48, "Little did I know"),
            (52, "That you were Romeo"),
            (55, "you were throwing pebbles"),
            (58, "And my daddy said"),
            (61, "Stay away from Juliet"),
            (65, "And I was crying"),
            (68, "on the staircase"),
            (71, "begging you"),
            (74, "Please don't go"),
            (78, "And I said..."),
            (82, "Romeo take me"),
            (85, "somewhere we can be"),
            (88, "alone"),
            (92, "I'll be waiting"),
            (95, "all there's left to do"),
            (98, "is run"),
            (102, "You'll be the prince"),
            (105, "and I'll be the princess"),
            (109, "It's a love story"),
            (112, "baby just say yes"),
            (120, "♪ ♫ ♪ ♫ ♪ ♫ ♪"),
            (125, "End of Lyrics")
        ]
       
        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string("Love Story")
        lcd.cursor_pos = (1, 0)
        lcd.write_string("Playing...")
        
        heart = (
            0b00000,
            0b01010,
            0b11111,
            0b11111,
            0b01110,
            0b00100,
            0b00000,
            0b00000
        )
        lcd.create_char(0, heart)
        
        start_time = time.time()
        current_line = 0
        if mode != "Music":
            lcd.clear()
            break
        while current_line < len(lyrics) and mode == "Music":
            if get_dict["Stage"] :
                mode = get_dict["Stage"]
            elapsed = time.time() - start_time
            if current_line < len(lyrics) - 1 and elapsed >= lyrics[current_line + 1][0]:
                current_line += 1
                
            line = lyrics[current_line][1]
            if len(line) <= 16:
                lcd.cursor_pos = (0, 0)
                lcd.write_string(line.center(16))
                lcd.cursor_pos = (1, 0)
                lcd.write_string(" " * 16)
            else:
                parts = [line[i:i+16] for i in range(0, len(line), 16)]
                lcd.cursor_pos = (0, 0)
                lcd.write_string(parts[0])
                if len(parts) > 1:
                    lcd.cursor_pos = (1, 0)
                    lcd.write_string(parts[1])
            time.sleep(0.1)
            if mode != "Music":
                lcd.clear()
                break
        
def watch():
    global should_blink,mode,current_mode
    while mode == "Stopwatch":
        
        lcd.clear()

        
        running = False
        start_time = 0
        elapsed_time = 0
        last_display_time = 0
        LED_START = 18
        LED_STOP = 23
        LED_RESET = 24
        
        lcd.cursor_pos = (0,0)
        lcd.write_string("Stopwatch Ready")
        lcd.clear()
        lcd.cursor_pos = (1,0)
        lcd.write_string("SW1:Start/Stop SW2:Reset")
        lcd.clear()
        colon_char = (
            0b00000,
            0b00100,
            0b00000,
            0b00000,
            0b00100,
            0b00000,
            0b00000,
            0b00000
        )
        lcd.create_char(2, colon_char)
        if mode != "Stopwatch":
            button_callback(21)

        while True:
            if get_dict["Stage"] :
                mode = get_dict["Stage"]
                
            
            if mode != "Stopwatch":
                button_callback(21)
                break

                
                
            current_time = time.time()
            if GPIO.input(21) == 0:  
                time.sleep(0.2) 
                if running:
                    running = False
                    elapsed_time = current_time - start_time
                    GPIO.output(LED_STOP, GPIO.HIGH)
                    time.sleep(0.3)
                    GPIO.output(LED_STOP, GPIO.LOW)
                else:
                    running = True
                    start_time = current_time - elapsed_time
                    GPIO.output(LED_START, GPIO.HIGH)
                    time.sleep(0.3)
                    GPIO.output(LED_START, GPIO.LOW)
            
            if GPIO.input(20) == 0:  
                time.sleep(0.1)  
                if not running:
                    
                    elapsed_time = 0
                    GPIO.output(LED_RESET, GPIO.HIGH)
                    time.sleep(0.3)
                    GPIO.output(LED_RESET, GPIO.LOW)
                    lcd.clear()
                    lcd.cursor_pos = (0,0)
                    lcd.write_string("00:00:00.000")
            if running:
                display_time = elapsed_time + (current_time - start_time)
            else:
                display_time = elapsed_time
            hours = int(display_time // 3600)
            minutes = int((display_time % 3600) // 60)
            seconds = display_time % 60
            milliseconds = int((seconds - int(seconds)) * 1000)
            seconds = int(seconds)
            
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
            
            lcd.cursor_pos = (0,0)
            lcd.write_string(time_str)
            lcd.cursor_pos = (1,0)
            if running:
                lcd.write_string("Run  SW1:Stop ")
            else:
                lcd.write_string("StopSW1:Start")
            if should_blink and int(current_time) % 2 == 0:
                lcd.cursor_pos = (0,2)
                lcd.write_string("\x02")  
                lcd.cursor_pos = (0,5)
                lcd.write_string("\x02")  
            else:
                lcd.cursor_pos = (0,2)
                lcd.write_string(" ")
                lcd.cursor_pos = (0,5)
                lcd.write_string(" ")
            if not running and GPIO.input(21) == 0:
                start_press = time.time()
                while GPIO.input(21) == 0:
                    if time.time() - start_press > 1.0:  
                        break
                    time.sleep(0.1)
                if time.time() - start_press > 1.0:
                    break
            
            time.sleep(0.01)
        if mode != "Stopwatch":
            
            break
            button_callback(21)
            current_mode= "Part"

               
    
     
def alarm():
    global alarm_triggered
    lcd.clear()
    lcd.cursor_pos = (0, 0)
    lcd.write_string("12:30 PM")
    lcd.cursor_pos = (1, 0)
    lcd.write_string("Time to lunch!")
    for _ in range(5):
        GPIO.output(18, GPIO.HIGH)
        GPIO.output(26, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(18, GPIO.LOW)
        GPIO.output(26, GPIO.LOW)
        time.sleep(0.3)
    
    alarm_triggered = True    
        
def emoji():
    smiley=(
        0b00000,
        0b00000,
        0b01010,
        0b00000,
        0b00000,
        0b10001,
        0b01110,
        0b00000
    )

    sad=(
        0b00000,
        0b00000,
        0b01010,
        0b00000,
        0b01110,
        0b10001,
        0b10001,
        0b00000
    )

    lcd.create_char(0,smiley)
    lcd.create_char(1,sad)
    
def mqtt_button_message(client,userdata,msg):
    global get_dict
    try:
        p_msg = str(msg.payload.decode("utf-8"))
        get_dict = json.loads(p_msg)
        print(f"Updated receive_dict: {get_dict}")
    except Exception as e:
        print(f"Error processing message: {e}")
 
def mqtt_on_message(client, userdata, msg):
    global receive_dict,d_msg
    try:
        d_msg = str(msg.payload.decode("utf-8"))
        receive_dict = json.loads(d_msg)
        
        print(f"Updated receive_dict: {receive_dict}")
        
        
    except Exception as e:
        print(f"Error processing message: {e}")
def publisher():
    global receive_dict, last_publish_time_true, last_publish_time_false, last_start_status, last_moved_status
    if 'last_start_status' not in globals():
        last_start_status = None
    if 'last_moved_status' not in globals():
        last_moved_status = None
        
    mqtt_broker = "ia.ic.polyu.edu.hk" 
    mqtt_port = 1883 
    mqtt_qos = 1 
    mqtt_topic = "C05"
    
    if not receive_dict:
        return
        
    current_time = time.time()
    current_start = receive_dict.get("Start")
    current_moved = receive_dict.get("MOVED")
    if current_moved == "Yes" and last_moved_status != "Yes":
        print("MOVED status changed to Yes - publishing immediately")
        message_data = receive_dict.copy()
        message_data["PublishTime"] = time.strftime("%Y-%m-%d %H:%M:%S")
        message_data["StatusChange"] = True 
        message_data["ChangeReason"] = "MOVED_Yes"
        
        jsonData = json.dumps(message_data)
        try:
            mqtt_client.publish(mqtt_topic, jsonData, mqtt_qos)
            print(f"Published MOVED=Yes message to {mqtt_topic}: {jsonData}")
            last_moved_status = current_moved
            return
        except Exception as e:
            print(f"Error publishing MOVED=Yes message: {e}")
    if current_start != last_start_status:
        print(f"Start status changed from {last_start_status} to {current_start}")
        message_data = receive_dict.copy()
        message_data["PublishTime"] = time.strftime("%Y-%m-%d %H:%M:%S")
        message_data["StatusChange"] = True 
        message_data["ChangeReason"] = "START_Change"
        
        jsonData = json.dumps(message_data)
        
        try:
            mqtt_client.publish(mqtt_topic, jsonData, mqtt_qos)
            print(f"Published status change message to {mqtt_topic}: {jsonData}")
            
            if current_start == "True":
                last_publish_time_true = current_time
            else:
                last_publish_time_false = current_time
                
        except Exception as e:
            print(f"Error publishing status change message: {e}")
        
        last_start_status = current_start
        last_moved_status = current_moved  
        return 
    
    if current_start == "True":
        interval = 60  
        last_publish_time = last_publish_time_true
    else:
        interval = 300  
        last_publish_time = last_publish_time_false
        
    time_since_last_publish = current_time - last_publish_time if last_publish_time else interval
    
    if time_since_last_publish >= interval:
        message_data = receive_dict.copy()
        message_data["PublishTime"] = time.strftime("%Y-%m-%d %H:%M:%S")
        message_data["TimeSinceReceived"] = time_since_last_publish
        message_data["StatusChange"] = False  
        message_data["ChangeReason"] = "Interval_Publish"
        
        jsonData = json.dumps(message_data)
        
        try:
            mqtt_client.publish(mqtt_topic, jsonData, mqtt_qos)
            print(f"Published interval message to {mqtt_topic}: {jsonData}")
            
            if current_start == "True":
                last_publish_time_true = current_time
            else:
                last_publish_time_false = current_time
                
        except Exception as e:
            print(f"Error publishing interval message: {e}")
        
        last_moved_status = current_moved  
if __name__ == "__main__":
    ######
    ######
    global receive_dict, d_msg, last_moved_status 
    global mode, current_mode, alarm_triggered     
    alarm_triggered = False  
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    lcd = CharLCD('PCF8574',0x27)
    lcd.cursor_pos = (0,0)
    output_channel = [8,25,24,23,18] 
    input_channel = [20,21]
    BUZ_GPIO = 26
    DHT_SENSOR = Adafruit_DHT.DHT11
    DHT_PIN = 4
    global current_mode, get_dict,d_msg
    current_mode = "Part"
    receive_dict = {}
    get_dict = {}
    last_moved_status = None
    
    ###
    BUTTON_GPIO = 20
    LED_GPIO2 = [18,24,8]
    LED_GPIO = [23,25]
    should_blink = True
    should_open = True
    ###
    GPIO.setup(BUZ_GPIO, GPIO.OUT)
    GPIO.setup(DHT_PIN, GPIO.IN, GPIO.PUD_UP)
    GPIO.setup(input_channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(output_channel, GPIO.OUT,initial=GPIO.LOW)   
    p = GPIO.PWM(BUZ_GPIO, 5)
    p.start(0)
    p.ChangeDutyCycle(0)
    adc = Adafruit_ADS1x15.ADS1115()
    GAIN = 1
    mqtt_broker = "ia.ic.polyu.edu.hk"
    mqtt_port = 1883
    mqtt_qos = 1
    mqtt_client = mqtt.Client("QQQ")
    mbtt_client = mqtt.Client("ppp")
    mqtt_client.connect(mqtt_broker, mqtt_port)
    mbtt_client.connect(mqtt_broker, mqtt_port)
    print("Connect to MQTT broker")
    Adafruit_DHT.DHT11=1
    #####
    #####
    
    GPIO.add_event_detect(21, GPIO.FALLING, callback=button_callback, bouncetime=200)
    GPIO.add_event_detect(20, GPIO.FALLING, callback=button_callback, bouncetime=200)
    GPIO.output(LED_GPIO2,GPIO.HIGH)
    lcd = CharLCD('PCF8574',0x27)
    lcd.cursor_pos = (1,0)
    lcd.clear()
    emoji()
    flag = True
    last_publish_time_true = None  
    last_publish_time_false = None
    last_start_status = None
   
    while True:
        
        mqtt_topic = "IC/TeamC05"
        mqtt_client.subscribe(mqtt_topic, mqtt_qos)
        mqtt_client.on_message = mqtt_on_message
        
        if receive_dict:
            publisher()
            
        mqtt_client.loop_start()
        mbtt_topic ="IC/C05"
        mbtt_client.subscribe(mbtt_topic, mqtt_qos)
        mbtt_client.on_message = mqtt_button_message
        
        mbtt_client.loop_start()
        now_time = time.strftime("%H:%M")
    
        if now_time == "12:30" and not alarm_triggered:
            mode = "Alarm"
            alarm()
        elif now_time != "12:30":
            alarm_triggered = False

        if should_open:
            GPIO.output(LED_GPIO2,GPIO.HIGH)
        if should_blink:
            GPIO.output(LED_GPIO, GPIO.HIGH)
            time.sleep(0.4)
        if should_blink:
            GPIO.output(LED_GPIO, GPIO.LOW)
            time.sleep(0.4)
     