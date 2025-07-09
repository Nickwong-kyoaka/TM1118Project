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




def mqtt_on_message(client, userdata, msg):
    global mode, current_mode
    if 

def button_callback(channel):
    global current_mode, mode
    if channel == 21 and mode == "data":
        curer
    if mode == "time":
        time()
        if mode = "stop"
    if mode = "stop":
        stop_watch()
        mode="init"
    if 

def mqtt_button_message(client, userdata, msg):
    if 

def main():
    DHT_SENSOR = Adafruit_DHT.DHT11
    DHT_PIN = 4
    mqtt_broker = "ia.ic.polyu.edu.hk"
    mqtt_port = 1883
    mqtt_qos = 1
    mqtt_client = mqtt.Client("iot-7296d")
    mqtt_client.connect(mqtt_broker, mqtt_port)
    print("Connect to MQTT broker")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    lcd = CharLCD('PCF8574',0x27)
    lcd.cursor_pos = (0,0)
    output_channel = [8,25,24,23,18] 
    input_channel = [20,21]
    BUZ_GPIO = 26
    GPIO.setup(BUZ_GPIO, GPIO.OUT)
    GPIO.setup(DHT_PIN, GPIO.IN, GPIO.PUD_UP)
    GPIO.setup(input_channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(output_channel, GPIO.OUT,initial=GPIO.LOW)
    p = GPIO.PWM(BUZ_GPIO, 100)
    p.start(0)
    p.ChangeDutyCycle(0)
    adc = Adafruit_ADS1x15.ADS1115()
    GAIN = 1
    Adafruit_DHT.DHT11=1
    global mode, current_mode
    GPIO.add_event_detect(21, GPIO.FALLING, callback=button_callback, bouncetime=200)
    GPIO.add_event_detect(20, GPIO.FALLING, callback=button_callback, bouncetime=200)
    #print("Publishing message", msg, "to topic", mqtt_topic)
    mode = "init"
    current_mode = "init"
    while True:
        mqtt_client.subscribe("IC/TeamC05", mqtt_qos)
        mqtt_client.on_message = mqtt_on_message
        mqtt_client.subscribe("IC/C05", mqtt_qos)
        mqtt_client.on_message = mqtt_button_message
        time.sleep(0.5)
        mqtt_client.loop_start()
        lcd.clear()

if __name__ == "__main__":
    main()
