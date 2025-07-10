import paho.mqtt.client as mqtt
from .models import Data_Receive
import json

mqtt_broker = "ia.ic.polyu.edu.hk" # Broker
mqtt_port = 1883 # Default
mqtt_qos = 1 # Quality of Service = 1
mqtt_topic = "C057"

def mqtt_on_message(client, userdata, msg):
# Do something
    d_msg = str(msg.payload.decode("utf-8"))
    iotData = json.loads(d_msg)
    print(iotData)
    print("Received message on topic %s : %s" % (msg.topic, iotData))
    k = Data_Receive(
        start = iotData["Start"],
        p_temp = iotData["Temp"],
        p_hum = iotData["Hum"],
        move = iotData["MOVED"],
    )
    k.save()
        
mqtt_client = mqtt.Client("appapaooo") # Create a Client Instance
mqtt_client.on_message = mqtt_on_message
mqtt_client.connect(mqtt_broker, mqtt_port) # Establish a connection to a broker
print("Connect to MQTT broker")
mqtt_client.subscribe(mqtt_topic, mqtt_qos)
mqtt_client.loop_start()