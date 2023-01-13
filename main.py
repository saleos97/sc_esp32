import network
import urequests
import ujson
import config
from umqtt.simple import MQTTClient
import time
import machine

# led declaration. The led uses the Pin 13 on our esp32
led = machine.Pin(13, machine.Pin.OUT)

# establish a Wifi connection
sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    while not sta_if.isconnected():
        pass
print('network config:', sta_if.ifconfig())
print('Wifi connected')

# Create MQTT Client (test-server)
mqttClient = MQTTClient('Aktormodul', 'test.mosquitto.org', port=1883)

# connect to mqtt server
mqttClient.connect()

# mqtt topic subscribe
topic_subscribe = 'iot/master'
topic_publish = 'iot/Actor-1/status'


# define function for the set_callback function
def on_message(topic, msg):
    message = msg.decode('utf-8')
    topic = topic.decode('utf-8')

    # reset the actor and publish a message to the broker
    if message == 'Master: Actor-1 reset.' and topic == 'iot/master':
        mqttClient.publish(topic_publish, 'Actor-1 is reset.', retain=False, qos=0)
        time.sleep(2)
        machine.reset()
    else:
        print('No message')


# set the callback function for the mqtt client. This mean if we receive a message the function 'on_message' will be
# called
mqttClient.set_callback(on_message)

# subscribe the topic
mqttClient.subscribe(topic_subscribe, qos=0)

# After turning on the actor modul.
mqttClient.publish(topic_publish, 'Actor-1 is ready.', retain=False, qos=0)

# create the post_data. This json will be sent over Infura to call the smart contract
post_data = ujson.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                         "params": [{"from": config.ADDRESS, "to": config.CONTRACT_ADDRESS, "data": "0xa5480959"},
                                    "latest"]})


# send request to the infura API to retrieve the led variable
def read_led():
    response = urequests.post(config.RPC_URL, headers={'content-type': 'application/json'}, data=post_data)
    result = response.json()['result']
    led_on = int(result, 16)
    if led_on == 1:
        led.value(1)
        mqttClient.publish(topic_publish, 'Actor-1 is on.', retain=False, qos=0)

    else:
        led.value(0)
        mqttClient.publish(topic_publish, 'Actor-1 is off.', retain=False, qos=0)


while True:
    mqttClient.check_msg()
    read_led()
    time.sleep(10)
    print("waiting...")
