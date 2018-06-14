import cv2
import facerecognition
import Queue
import numpy as np
import time,os
from multiprocessing import Process, Queue
import struct
import paho.mqtt.client as mqtt
import argparse
import SocketServer
import time
from PIL import Image


parser = argparse.ArgumentParser()
parser.add_argument('--svr', type=str,
                    help='The ip for laptop training server')

facerecg = facerecognition.FaceRecognition("./models", 0.63)

HOST = ''
PORT = 21575
ADDR = (HOST, PORT)
bufSize = 4080


def recognize(rawData):
    img = Image.frombytes('RGB', (480, 272), rawData, 'raw', 'RGB;16')
    npimg = np.rot90(np.array(img), -1)

    image_char = npimg.astype(np.uint8).tostring()
    rets = facerecg.recognize(npimg.shape[0], npimg.shape[1], image_char)

    if rets is None or len(rets) == 0:
        rect = [0,0,0,0]
        name = None
    else:
        rect = rets[0]['rect']
        name = rets[0]['name']
    if name is not None and name != " " and name != "":
        buff = struct.pack("iiii{}s".format(len(name)), rect[0], rect[1], rect[2], rect[3],str(name))
    else:
        buff = struct.pack("iiii",rect[0], rect[1], rect[2], rect[3])

    return buff

def addperson(name, rawData):
    img = Image.frombytes('RGB', (480, 272), rawData, 'raw', 'RGB;16')
    npimg = np.rot90(np.array(img), -1)

    image_char = npimg.astype(np.uint8).tostring()
    ret = facerecg.add_person(name, npimg.shape[0], npimg.shape[1], image_char)

    return ret

newname = None
def mqttmsg(client, data, msg):
    global newname
    if msg.topic == "NXP_CMD_MODULE_UPDATE":
        pass
    elif msg.topic == "NXP_CMD_ADD_PERSON":
        print "NXP_CMD_ADD_PERSON", msg.payload
        newname = msg.payload
    elif msg.topic == "NXP_CMD_DEL_PERSON":
        print "NXP_CMD_DEL_PERSON", msg.payload
        ret = facerecg.del_person(msg.payload)


args = parser.parse_args()


img_size = 261120
class MyRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        broadmqtt = mqtt.Client()
        broadmqtt.connect("localhost", 1883, 60)
        broadmqtt.subscribe("NXP_CMD_MODULE_UPDATE", qos=1)
        broadmqtt.subscribe("NXP_CMD_ADD_PERSON", qos=1)
        broadmqtt.subscribe("NXP_CMD_DEL_PERSON", qos=1)
        broadmqtt.on_message = mqttmsg
        broadmqtt.loop_start()

        print '...connected from:', self.client_address
        conn = self.request
        global newname

        databuffer = None
        receving = False
        while True:
            buf = conn.recv(bufSize)
            if len(buf) == 5:
                if buf[0] == '\x01' and buf[1] == '\x02' and buf[2] == '\x03' and buf[3] == '\x04' and buf[4] == '\x05':
                    databuffer = bytes()
                    receving = True
                elif buf[0] == '\x06' and buf[1] == '\x07' and buf[2] == '\x08' and buf[3] == '\x09' and buf[4] == '\x0a':
                    pass
                else:
                    pass

            elif receving:
                databuffer += buf
                if len(databuffer) >= img_size:
                    if newname:
                        ret = addperson(newname, databuffer)
                        newname = None
                    else:
                        buff = recognize(databuffer)
                        conn.sendall(buff)
                    receving = False

def tcpServerProcess():
    tcpServ = SocketServer.ThreadingTCPServer(ADDR, MyRequestHandler)
    print 'waiting for connection...'
    tcpServ.serve_forever()

def startTcpServer():
    p2 = Process(target = tcpServerProcess, args=())
    p2.start()

tcpServ = SocketServer.ThreadingTCPServer(ADDR, MyRequestHandler)
print 'waiting for connection...'
tcpServ.serve_forever()
