import paho.mqtt.client as mqtt
from .models import Event
from .models import Event2
import json
print("Connect1111")  
ID ='C05'
mqtt_broker = "broker.hivemq.com" # Broker
mqtt_port = 1883 # Default
mqtt_qos = 1 # Quality of Service = 1
mqtt_topic = "iot/teamC03"  
def mqtt_on_message(client, userdata, msg):
# Do something
    d_msg = str(msg.payload.decode("utf-8"))
    iotData = json.loads(d_msg)
    print(iotData)
    if iotData["node_id"] == ID:
        print("Received message on topic %s : %s" % (msg.topic, iotData))
        p = Event2(
            node_id = iotData["node_id"],
            #loc = iotData["loc"],
            #temp = iotData["temp"],
            #hum = iotData["hum"],
            #light = iotData["light"],
            #snd = iotData["snd"]
        )
        p.save()
        k = Event(
            node_id = iotData["node_id"],
            loc = iotData["loc"],
            temp = iotData["temp"],
            hum = iotData["hum"],
            light = iotData["light"],
            snd = iotData["snd"]
        )
        k.save()

    
mqtt_client = mqtt.Client("ffff2556ddfdsfs") # Create a Client Instance
mqtt_client.on_message = mqtt_on_message
mqtt_client.connect(mqtt_broker, mqtt_port) # Establish a connection to a broker
print("Connect to MQTT broker")
mqtt_client.subscribe(mqtt_topic, mqtt_qos)
mqtt_client.loop_start()