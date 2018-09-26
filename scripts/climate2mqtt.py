# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import subprocess
import json
import yaml
import totalcomfort
from totalcomfort import TotalComfortAction

gmode = 0

#https://gist.github.com/ghostbitmeta/694934062c0814680d52

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flag, rc):
	print("Connected with result code %s" % (str(rc)))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
	client.subscribe("hvac/central/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("Topic: ", msg.topic+'\nMessage: '+str(msg.payload, encoding='ascii'))
    {
        "hvac/central/temperature/set": set_temperature,
        "hvac/central/mode/set": set_mode,
		"hvac/central/fan/set": set_fan,
		"hvac/central/status": get_status,
    }.get(str(msg.topic), wrong_topic)(client, msg)

def wrong_topic(client, msg):
	print(str(msg.topic))

def set_temperature(client, msg):
	global gmode
	print("set_temperature, gmode={0}".format(gmode))
	client.publish("hvac/central/temperature/state", str(msg.payload, encoding='ascii'))    
	action = (TotalComfortAction.COOL) if (gmode == 3) else TotalComfortAction.HEAT
	totalcomfort.execute(action, str(msg.payload));

def get_status(client, msg):
	global gmode
	print("get_status")
    
	j = totalcomfort.execute(TotalComfortAction.JSON);
    
    #todo check if i = None
    
	client.publish("hvac/central/temperature/current", j['latestData']['uiData']["DispTemperature"])
	gmode = j['latestData']['uiData']["SystemSwitchPosition"]
	if (gmode == 3):
		client.publish("hvac/central/temperature/state", j['latestData']['uiData']["CoolSetpoint"])
	else:
		client.publish("hvac/central/temperature/state", j['latestData']['uiData']["HeatSetpoint"])
	
	fan_state = ("auto") if (j['latestData']['fanData']["fanMode"] == "0") else "always_on"
	client.publish("hvac/central/fan/state", fan_state)
	mode = "bleh"

	if (gmode == 0):
		mode = 'emheat'
	if (gmode == 1):
		mode = 'heat'
	if (gmode == 2):
		mode = 'stop'
	if (gmode == 3):
		mode = 'cool'
	print(mode)
	client.publish("hvac/central/mode/state", mode)

def set_mode(client, msg):
	print("set_mode")
	client.publish("hvac/central/mode/state", str(msg.payload, encoding='ascii'))
	mode = 2

	print(str(msg.payload, encoding='ascii'))

	if (str(msg.payload, encoding='ascii').startswith('emheat')):
		mode = 0
	if (str(msg.payload, encoding='ascii').startswith('heat')):
		mode = 1
	if (str(msg.payload, encoding='ascii').startswith('cool')):
		mode = 3

	totalcomfort.execute(TotalComfortAction.MODE, mode)

def set_fan(client, msg):
	print("set_fan")
	client.publish("hvac/central/fan/state", str(msg.payload, encoding='ascii'))
	fanmode = '0' if (str(msg.payload, encoding='utf-8').startswith('auto')) else '1'
	totalcomfort.execute(TotalComfortAction.FAN, fanmode)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

## TODO: relative path to file

#dir = os.path.dirname(os.path.realpath(__file__))
credentials = yaml.load(open('./credentials.yaml'))
client.connect(credentials['mqtt_broker_host'], 1883, 60)

client.publish("hvac/central/status", "")

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
