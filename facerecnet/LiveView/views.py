from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse, HttpResponseServerError
from django.contrib import admin
import cv2
import threading
from queue import Queue
from multiprocessing.pool import ThreadPool
from API import FaceRecAPI



working_file = "/home/user/Documents/dlib/models/"
models = [working_file + "shape_predictor_5_face_landmarks.dat",
          working_file + "dlib_face_recognition_resnet_model_v1.dat",
          working_file + "shape_predictor_68_face_landmarks.dat"]


stream_server_pool = ThreadPool(processes=1)
frameQ = Queue(maxsize=5)


class Recognition:

    def startrecognition(self):
        try:
            if self.fr_thread.isAlive():
                return True
            else:
                self.x = FaceRecAPI.FaceRecognition(models)
                self.x.load_files()
                self.stream_thread = StreamThread()
                self.arduino_thread = ArduinoThread()
                self.process_pool = ThreadPool(processes=1)
                self.access_pool = ThreadPool(processes=1)
                self.fr_thread = FaceRecognitionThread()
                self.fr_thread.start()
                return False
        except AttributeError:
            self.x = FaceRecAPI.FaceRecognition(models)
            self.x.load_files()
            self.stream_thread = StreamThread()
            self.arduino_thread = ArduinoThread()
            self.process_pool = ThreadPool(processes=1)
            self.access_pool = ThreadPool(processes=1)
            self.fr_thread = FaceRecognitionThread()
            self.fr_thread.start()
            return False

rc = Recognition()


class FaceRecognitionThread(threading.Thread):
    def __init__(self):
        super(FaceRecognitionThread, self).__init__(target=facerecognition, name="FaceRecThread")
        self._stop_event = threading.Event()

    def destop(self):
        self._stop_event.clear()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class ArduinoThread(threading.Thread):
    def __init__(self):
        super(ArduinoThread, self).__init__(target=rc.x.arduino_server, name="ArduinoThread", daemon=True)
        self._stop_event = threading.Event()

    def destop(self):
        self._stop_event.clear()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class StreamThread(threading.Thread):
    def __init__(self):
        super(StreamThread, self).__init__(target=rc.x.read_stream, name="StreamThread", daemon=True)
        self._stop_event = threading.Event()

    def destop(self):
        self._stop_event.clear()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()



def facerecognition():
    print("face recognition is starting up")
    try:
        rc.x.cap
    except AttributeError:
        rc.x.grab_cap()

    rc.arduino_thread.daemon = True
    rc.stream_thread.daemon = True
    rc.stream_thread.start()
    rc.arduino_thread.start()
    print("Face Recognition is running")
    while True:
        if rc.fr_thread.stopped():
            rc.arduino_thread.stop()
            rc.stream_thread.stop()
            rc.process_pool.terminate()
            rc.access_pool.terminate()
            stream_server_pool.terminate()
            frameQ.task_done()
            rc.arduino_thread.join()
            rc.stream_thread.join()
            rc.process_pool.join()
            stream_server_pool.join()
            rc.access_pool.join()
            rc.x.arduino_server_pool.terminate()
            rc.x.arduino_server_pool.join()

            print("all killed")
            break
        process = rc.process_pool.apply_async(rc.x.process)
        labels, frame = process.get()
        access = rc.access_pool.apply_async(rc.x.access, args=(labels, frame))
        # cv2.imshow("test", frame)
        # cv2.waitKey(1)
        if frameQ.full():
            continue
        frameQ.put(frame)
    rc.arduino_thread.destop()
    rc.stream_thread.destop()
    rc.fr_thread.destop()
    rc.x.cap.release()
    cv2.destroyAllWindows()
    return



def stream_server():

    while True:
        image = frameQ.get()
        ret, jpeg = cv2.imencode('.jpg', image)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@login_required(login_url='/accounts/login')
def stream(request):
    try:
        rc.startrecognition()
        return StreamingHttpResponse(stream_server(), content_type="multipart/x-mixed-replace;boundary=frame")
    except HttpResponseServerError as e:
        print("aborted")


@login_required(login_url='/accounts/login')
def index(request):
    if rc.startrecognition():
        message = "Face recognition is already running."
    else:
        message = "Face recognition has been started"
    admin.ModelAdmin.message_user(admin.ModelAdmin, request, message)
    return HttpResponseRedirect("../admin")


@login_required(login_url='/accounts/login')
def stop_recognition(request):
    rc.fr_thread.stop()
    message = "Face recognition has been stopped"
    admin.ModelAdmin.message_user(admin.ModelAdmin, request, message)
    return HttpResponseRedirect("../admin")
