import os
import cv2
import dlib
import pafy
import base64
import atexit
import eventlet


class Video(object):

        def __init__(self, socketio, source='cam', url=None, vidfile=None):
            self.cap = None
            self.frame = None
            self.detector = None
            self.frame = None
            self.socketio = socketio
            self.source = source
            self.url = url
            self.vidfile = vidfile
            self.fps = 0
            self.delay = 10    # nominal 10ms delay for camera video capture
            self.min_delay = 10
            self.max_delay = 1000
            self.fheight = 720
            self.fwidth = 1280          
            self.flength = 0 
            self.fplay = 1.0;
            self.initFlag = False
            self.runFlag = False
            self.detectFlag = False
            self.enableTracking = False   # set by websockets from user
            self.trackFlag = False  # set by program after face recognition if tracking is enabled
            atexit.register(self.cleanup)

        def cleanup(self):
            if not self.cap: return
            if self.cap.isOpened():
                self.cap.release()
            cv2.destroyAllWindows()

        def play(self):
            # if video already running then return
            if self.initFlag: 
                self.runFlag = True
                return
            if self.source == 'cam':
                self.cap = cv2.VideoCapture(0)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.fwidth)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.fheight)
                # get frames per second and convert to delay between frames for playback
                self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            elif self.source == 'youtube' or self.source == 'vidfile':
                if self.source == 'youtube':
                    video = pafy.new(self.url)
                    best = video.getbest(preftype="mp4")
                    self.cap = cv2.VideoCapture(best.url)
                else:
                    self.cap = cv2.VideoCapture(self.vidfile)
                # get video information
                self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
                self.delay  = int(1000 / self.fps)
                self.min_delay = int(int(int(int(self.delay / 2) / 2) / 2) / 2)
                self.max_delay = self.delay * 4
            else:
                pass

            print("Frames per second: {0}".format(self.fps))
            print("Delay between frames: {0}".format(self.delay))
    
            # get frame height and width
            self.fwidth = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH ))
            self.fheight = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print("Frame Height: {0}, Width: {1}".format(self.fheight, self.fwidth))
    
            # get video length - number of frames
            self.flength = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            print("Number of Frames in Video: {0}".format(self.flength))
            # send status to webpage
            self.socketio.emit('message', {'type': 'videoInfo', 'fps': self.fps, 'delay': self.delay, 'fwidth': self.fwidth,'fheight': self.fheight, 'fnumber': self.flength, 'fplay': self.fplay}, namespace='/comm')

            # start loop with video capture
            eventlet.spawn_n(self.streamVideo)
            self.initFlag = True
            self.runFlag = True


        def pause(self):
            self.runFlag = False


        def stop(self):
            self.initFlag = False
            self.runFlag = False


        def fast(self):
            if self.source == 'cam': return
            if self.delay >= 2 * self.min_delay:
                self.delay = int(self.delay / 2)
                self.fps *= 2
                self.fplay *= 2.0
                self.socketio.emit('message', {'type': 'videoInfo', 'fps': self.fps, 'delay': self.delay, 'fwidth': self.fwidth,'fheight': self.fheight, 'fnumber': self.flength, 'fplay': self.fplay}, namespace='/comm')
            else:
                print("Frames per second is already max...")


        def slow(self):
            if self.source == 'cam': return
            if self.delay <= self.max_delay / 2:
                self.delay = 2 * self.delay
                self.fps /= 2
                self.fplay /= 2.0
                self.socketio.emit('message', {'type': 'videoInfo', 'fps': self.fps, 'delay': self.delay, 'fwidth': self.fwidth,'fheight': self.fheight, 'fnumber': self.flength, 'fplay': self.fplay}, namespace='/comm')
            else:
                print("Frames per second is already min...")


        def save(self):
            pass
         

        def streamVideo(self):
            # Read until video is completed
            frame_ctr = 0
            while self.cap.isOpened():
                if self.runFlag: 
                    # Capture frame-by-frame
                    r1, self.frame = self.cap.read()
                    if r1:
                        frame_ctr += 1
                        percent_complete = 100.0
                        if self.source == 'youtube' or self.source == 'vidfile':
                            percent_complete = 100.0 * frame_ctr / self.flength
                            frame_ctr = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                        # run tracking if enabled
                        if self.trackFlag:


                        # make jpeg from frame and attach to generator connected to http response
                        r2, jpeg = cv2.imencode('.jpg', self.frame)                      
                        if r2:
                            # print("bframe", frame_ctr)
                            self.socketio.emit('frame', {'image': 'data:image/jpeg;charset=utf-8;base64,' + base64.b64encode(jpeg).decode('utf-8'), 
                                                    'width': self.fwidth, 'height': self.fheight, 'frameCtr': frame_ctr, 'percentComplete': percent_complete}, namespace='/video')
                    else:
                        print("Error in OpenCV video capture...") 
                        # stop looping (must restart method to view video again)
                        break
                else:
                    if self.detectFlag:
                        self.detectFace()
                        r2, jpeg = cv2.imencode('.jpg', self.frame)                      
                        if r2:
                            self.socketio.emit('frame', {'image': 'data:image/jpeg;charset=utf-8;base64,' + base64.b64encode(jpeg).decode('utf-8'), 
                                                         'width': self.fwidth, 'height': self.fheight, 'frameCtr': frame_ctr, 'percentComplete': percent_complete}, namespace='/video')
                            self.detectFlag = False
                            if self.enableTracking:
                                self.trackFlag = True

                # allow greenlet to yield and delay with cv2.waitkey
                # exit streaming video if stop has been pressed (initFlag = false)
                if not self.initFlag: break
                eventlet.sleep(0) 
                cv2.waitKey(self.delay) 


        def detectFace(self):
            '''
            Face detectors - four types:
            (1) Haar from OpenCV
            (2) DNN from OpenCV
            (3) HoG from Dlib
            (4) CNN from Dlib

            Return bounding boxes for faces
            '''
            bounding_box = []
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            current = os.getcwd()
            if self.detector == 'Haar':
                face_cascade = cv2.CascadeClassifier(current + "\\data\\" + "haarcascade_frontalface_default.xml")
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                save = True
                for (x1,y1,w,h) in faces:
                    x2 = x1 + w
                    y2 = y1 + h
                    if save:
                        bounding_box = [x1, y1, x2, y2]
                        save = False
                    cv2.rectangle(self.frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    index += 1
            elif self.detector == 'DNN':
                modelFile = current + "\\data\\" + "opencv_face_detector_uint8.pb"
                configFile = current + "\\data\\" + "opencv_face_detector.pbtxt"
                net = cv2.dnn.readNetFromTensorflow(modelFile, configFile)
                blob = cv2.dnn.blobFromImage(self.frame, 1.0, (300, 300), [104, 117, 123], False, False)
 
                net.setInput(blob)
                detections = net.forward()
                save = True
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    if confidence > 0.75:
                        x1 = int(detections[0, 0, i, 3] * self.fwidth)
                        y1 = int(detections[0, 0, i, 4] * self.fheight)
                        x2 = int(detections[0, 0, i, 5] * self.fwidth)
                        y2 = int(detections[0, 0, i, 6] * self.fheight)
                        if save:
                            bounding_box = [x1, y1, x2, y2]
                            save = False
                        cv2.rectangle(self.frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

            elif self.detector == 'HoG':
                hogFaceDetector = dlib.get_frontal_face_detector()
                faceRects = hogFaceDetector(self.frame, 0)  # second number is times to upscale image for better detection
                save = True
                for faceRect in faceRects:
                    x1 = faceRect.left()
                    y1 = faceRect.top()
                    x2 = faceRect.right()
                    y2 = faceRect.bottom()
                    if save:
                        bounding_box = [x1, y1, x2, y2]
                        save = False
                    cv2.rectangle(self.frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            elif self.detector == 'CNN':
                cnnFaceDetector = dlib.cnn_face_detection_model_v1(current + "\\data\\" + "mmod_human_face_detector.dat")
                faceRects = cnnFaceDetector(self.frame, 0)  # second number is times to upscale image for better detection
                save = True
                for faceRect in faceRects:
                    x1 = faceRect.rect.left()
                    y1 = faceRect.rect.top()
                    x2 = faceRect.rect.right()
                    y2 = faceRect.rect.bottom()
                    if save:
                        bounding_box = [x1, y1, x2, y2]
                        save = False
                    cv2.rectangle(self.frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            else:
                print("No detector is recognized...")
                self.socketio.emit('message', {'type': 'status', 'msg': 'No detector is recognized... Select detector from list...'}, namespace='/comm')

            return bounding_box

        
        def draw_border(self, img, pt1, pt2, color, thickness, r, d):
            x1,y1 = pt1
            x2,y2 = pt2

            # Top left
            cv2.line(img, (x1 + r, y1), (x1 + r + d, y1), color, thickness)
            cv2.line(img, (x1, y1 + r), (x1, y1 + r + d), color, thickness)
            cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)

            # Top right
            cv2.line(img, (x2 - r, y1), (x2 - r - d, y1), color, thickness)
            cv2.line(img, (x2, y1 + r), (x2, y1 + r + d), color, thickness)
            cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)

            # Bottom left
            cv2.line(img, (x1 + r, y2), (x1 + r + d, y2), color, thickness)
            cv2.line(img, (x1, y2 - r), (x1, y2 - r - d), color, thickness)
            cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)

            # Bottom right
            cv2.line(img, (x2 - r, y2), (x2 - r - d, y2), color, thickness)
            cv2.line(img, (x2, y2 - r), (x2, y2 - r - d), color, thickness)
            cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)




