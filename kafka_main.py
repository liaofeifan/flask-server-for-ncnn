import cv2
import facerecognition
import numpy as np
import time,os
import argparse
#from kafka import SimpleProducer, KafkaClient
import paho.mqtt.client as mqtt


#connect to Kafka
#kafka = KafkaClient('10.193.20.94:9092')
#producer = SimpleProducer(kafka)
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers='10.193.20.94:9092')
# Assign a topic
topic = 'NXP_RECG_PEOPLE_GATE'

os.environ["CAP_PROP_FRAME_WIDTH"] = "640"
os.environ["CAP_PROP_FRAME_HEIGHT"] = "480"

parser = argparse.ArgumentParser()
parser.add_argument('--dev', type=str, required=True,
                    help='[usb|"url" of IP camera]input video device')
parser.add_argument('--time', type=int, default=1,
                    help='How long to send a recognition msg')
parser.add_argument('--location', type=str, default="gate", choices=["gate", "livingroom"],
                    help='The camera location')
args = parser.parse_args()

print("Initialzing camera.")
if args.dev == 'usb':
    cap = cv2.VideoCapture(1)
    print("Using onboard usb camera")
else:
    url = "rtsp://admin:a12345678@10.193.20.183/h264/ch1/sub/av_stream"
    cap = cv2.VideoCapture(url)
    print("Using ip camera with url(s)", url)

if args.location == "gate":
    msg_topic = "PLAY_HELLO"
else:
    msg_topic = "START_RECG"

def rotate(image, angle, center=None, scale=1.0):
    (h, w) = image.shape[:2]

    if center is None:
        center = (w / 2, h / 2)

    M = cv2.getRotationMatrix2D(center, angle, scale)
    rotated = cv2.warpAffine(image, M, (w, h))

    return rotated

facerecg = facerecognition.FaceRecognition("./models", 0.70)

mqttclient = mqtt.Client()
mqttclient.connect('localhost', 1883, 60)
mqttclient.loop_start()

sndtime = args.time * 60
beforetime = 0

rets = []
if cap.isOpened():
    while True:
        ret, image = cap.read()
        if not ret:
            continue

        #print "image.shape[0:3] =", image.shape[0:3]
        #image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        #print "image.ndim", image.ndim
        image_char = image.astype(np.uint8).tostring()
        #print "image.shape[0:2] =", image.shape[0:2]
        #print image

        rets = facerecg.recognize(image.shape[0], image.shape[1], image_char)
        print(rets)

        for ret  in  rets:
            name = ret['name']
            if(name == "gf"):
                currenttime = time.time()
                if (currenttime - beforetime >= sndtime):
                    beforetime = currenttime
                    crop = cv2.resize(image, (0, 0), fx=0.25, fy=0.25)
                    _, jpeg = cv2.imencode('.png', crop)
                    mqttclient.publish(msg_topic, name)
                    #producer.send_messages(topic, "aaa")
                    producer.send(topic, jpeg.tobytes())
                    print("Send image")

