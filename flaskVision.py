'''
Created on May 6, 2019

@author: Barnwaldo
'''

import json
import time
import json
import cv2
import eventlet
from video import Video
from flask import Flask, request, render_template, Response
from flask_socketio import SocketIO


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.threaded = True
# app.config['DEBUG'] = True
socketio = SocketIO(app)

# default to web cam 0
vid = Video(socketio, source='cam')

# testing for CUDA - currently not built with CUDA (will revisit in the future)
# import dlib
# print(dlib.__version__)
# print(dlib.DLIB_USE_CUDA)
# print(cv2.__version__)
# print(cv2.getBuildInformation())

@app.route('/')
def index():
    #only by sending this page first will the client be connected to the socketio instance
    print(">> rendering index.html...")
    return render_template('index.html')

@socketio.on('connect', namespace='/comm')
def comm_connect():
    print('>> comm socketIO connected')
    # url = "https://www.youtube.com/watch?v=XvzNuw5VjBU"


@socketio.on('connect', namespace='/video')
def video_connect():
    print('>> video socketIO connected')

        
@socketio.on('message', namespace='/comm')
def comm_message(msg):
    global vid
    print(">> message received on comm socketIO: ", msg) 
    obj = json.loads(msg)
    msgType = obj['msgType']
    
    if msgType == 'source':
        vid.stop()
        vid.cleanup()
        player = obj['player']
        if player == 'webcam':
            vid = Video(socketio, source='webcam')
        elif player == 'youtube':
            vid = Video(socketio, source='youtube', url=obj['url'])
        elif player == 'vidfile':
            vid = Video(socketio, source='vidfile', vidFile=obj['fpath'])
        else:
            pass
    
    elif msgType == 'ioFile':
        inputFile = obj['input']
        outputFile = obj['output']
        filePath = obj['filePath']

    elif msgType == 'playerControl':
        selected = obj['selected']
        if selected == 'play':
            vid.play()
        elif selected == 'stop':
            vid.stop()
        elif selected == 'pause':
            vid.pause()
        elif selected == 'fast':
            vid.fast()
        elif selected == 'slow':
            vid.slow()
        else:
            pass
    elif msgType == 'detector':
        if not vid.initFlag:
            socketio.emit('message', {'type': 'status', 'msg': 'Start video for first time... Then pause before running face detector... '}, namespace='/comm')
        else:
            if vid.runFlag:
                socketio.emit('message', {'type': 'status', 'msg': 'Pause video before running face detector...'}, namespace='/comm')
            else:
                vid.detectFlag = True;
                vid.detector = obj['type']
    elif msgType == 'tracker':
        vid.enableTracking = True
        vid.tracker = obj['type']
    elif msgType == 'selectTrack':
        pass
    else:
        pass
    

@socketio.on('disconnect', namespace='comm')
def comm_disconnect():
    print('>> comm socketIO disconnected')


@socketio.on('disconnect', namespace='video')
def video_disconnect():
    print('>> video socketIO disconnected')


if __name__ == '__main__':
    socketio.run(app)
