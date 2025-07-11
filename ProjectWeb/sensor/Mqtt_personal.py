import paho.mqtt.client as mqtt
from .models import Data_Receive
import json
import uuid

mqtt_broker = "ia.ic.polyu.edu.hk"
mqtt_port = 1883
mqtt_qos = 1
mqtt_topic = "C05"

def mqtt_on_message(client, userdata, msg):
    try:
        d_msg = str(msg.payload.decode("utf-8"))
        iotData = json.loads(d_msg)
        print("Received message on topic %s : %s" % (msg.topic, iotData))
        
        if all(key in iotData for key in ["Start", "Temp", "Hum", "MOVED"]):
            k = Data_Receive(
                start=iotData["Start"],
                p_temp=iotData["Temp"],
                p_hum=iotData["Hum"],
                move=iotData["MOVED"],
            )
            k.save()
            
            if iotData["MOVED"] == "True":
                client.publish("TeamC05Alarm", json.dumps({"MOVED": "True"}))
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(mqtt_topic, mqtt_qos)
    else:
        print(f"Connection failed with code {rc}")

def on_disconnect(client, userdata, rc):
    print(f"Disconnected from MQTT broker with code {rc}. Reconnecting...")
    client.reconnect()

mqtt_client = mqtt.Client(f"app_{uuid.uuid4().hex}")
mqtt_client.on_message = mqtt_on_message
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

try:
    mqtt_client.connect(mqtt_broker, mqtt_port, keepalive=60)
    print("Connected to MQTT broker")
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")

mqtt_client.loop_start()