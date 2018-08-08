#!/usr/bin/env python
from importlib import import_module
import os,time
from flask import Flask, render_template, Response
import argparse
from flask_socketio import SocketIO,emit

parser = argparse.ArgumentParser()
parser.add_argument('--httpport', type=int,
                    help='The port for http server')
args = parser.parse_args()

if args.httpport != None:
    HTTP_PORT = args.httpport
else:
    HTTP_PORT = 5000

app = Flask(__name__)
socketio = SocketIO()
socketio.init_app(app)

from socket import *

HOST='127.0.0.1'
PORT=5050

udpsocket = socket(AF_INET,SOCK_DGRAM)
udpsocket.connect((HOST,PORT))

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index_web.html')

@socketio.on('request',namespace='/testnamespace')
def give_response(data):
    msg_type = data.get('type')
    msg_data = data.get('data')

    if (msg_type == "ADDPERSON_REQ"):
        print "TRAINSTART_REQ"
        udpsocket.sendall("ADD:" + str(msg_data))
    elif (msg_type == "DELPERSON_REQ"):
        print "DELPERSON_REQ"
        udpsocket.sendall("DEL:" + str(msg_data))
    elif (msg_type == "GETNAMES_REQ"):
        names = ["aaa"]
        emit('response',{'code':'200','msg': ",".join(names)})

if __name__ == '__main__':
    #websocket.startWebSocketServer(serverip)
    #app.run(host='0.0.0.0', threaded=True)
    #app.run(host='0.0.0.0', port=HTTP_PORT, threaded=True, ssl_context=(tls_crt, tls_key))
    socketio.run(app,debug=True,host='0.0.0.0',port=HTTP_PORT)
