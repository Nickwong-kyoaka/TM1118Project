# Mqtt_alarm.py
import paho.mqtt.client as mqtt
import json

mqtt_broker = "ia.ic.polyu.edu.hk"
mqtt_port = 1883
mqtt_qos = 1
mqtt_topic_publish = "IC/TeamC05Alarm"

class AlarmMQTT:
    def __init__(self):
        self.client = mqtt.Client("TeamC05AlarmPublisher")
        self.client.connect(mqtt_broker, mqtt_port)
    
    def publish_alarm(self, alarm_data):
        """
        Publish alarm data to MQTT topic
        alarm_data should be a dictionary containing:
        {
            'location': str,
            'node_id': str,
            'sensor': str,
            'value': float,
            'threshold': str,
            'timestamp': str
        }
        """
        try:
            payload = json.dumps(alarm_data)
            self.client.publish(mqtt_topic_publish, payload, qos=mqtt_qos)
            print(f"Published alarm to {mqtt_topic_publish}: {payload}")
        except Exception as e:
            print(f"Error publishing alarm: {str(e)}")

# Global instance to be used across the application
alarm_mqtt = AlarmMQTT()