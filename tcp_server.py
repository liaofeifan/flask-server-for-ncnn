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


def rgb2png(training, rawData):
    name = None

    imgSize = (480, 272)

    img = Image.frombytes('RGB', imgSize, rawData, 'raw', 'RGB;16')
    npimg = np.rot90(np.array(img), -1)

    image_char = npimg.astype(np.uint8).tostring()
    rets = facerecg.recognize(npimg.shape[0], npimg.shape[1], image_char)
    print rets, npimg.shape[0], npimg.shape[1]
    if rets is None or len(rets) == 0:
        rect = [0,0,0,0]
    elif training:
        rect = rets[0]['rect']
    else:
        rect = rets[0]['rect']
        name = rets[0]['name']
    if name is not None and name != " " and name != "":
        buff = struct.pack("iiii{}s".format(len(name)), rect[0], rect[1], rect[2], rect[3],str(name))
    else:
        buff = struct.pack("iiii",rect[0], rect[1], rect[2], rect[3])

    return buff

def modulesUpdate(client, data, msg):
    print("Get module update msg")
    facerecg.moduleUpdate("")

args = parser.parse_args()


img_size = 261120
class MyRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        if args.svr:
            broadmqtt = mqtt.Client()
            broadmqtt.connect(args.svr, 1883, 60)
            broadmqtt.subscribe("NXP_CMD_MODULE_UPDATE", qos=1)
            broadmqtt.on_message = modulesUpdate
            broadmqtt.loop_start()
        print '...connected from:', self.client_address
        conn = self.request
        training = False
        name = None

        databuffer = None
        receving = False
        while True:
            buf = conn.recv(bufSize)
            if len(buf) == 5:
                if buf[0] == '\x01' and buf[1] == '\x02' and buf[2] == '\x03' and buf[3] == '\x04' and buf[4] == '\x05':
                    databuffer = bytes()
                    receving = True
                else:
                    pass

                if training:
                    ret = facerecg.getTrainStatus()
                    if ret[0] == 0:
                        training = False
                        buff = struct.pack("cccc", 'c','c','c','c')
                        conn.sendall(buff)
            elif receving:
                databuffer += buf
                if len(databuffer) >= img_size:
                    buff = rgb2png(training, databuffer)
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
