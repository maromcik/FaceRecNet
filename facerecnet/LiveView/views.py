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
from webpush import send_user_notification
import time
from facerecnet import views as frviews

working_file = "/home/user/Documents/dlib/models/"
models = [working_file + "shape_predictor_5_face_landmarks.dat",
          working_file + "dlib_face_recognition_resnet_model_v1.dat",
          working_file + "shape_predictor_68_face_landmarks.dat"]


frameQ = Queue(maxsize=5)
arduino_lock = threading.Event()
arduino_lock.clear()


class RecognitionThreads:

    def __init__(self):
        self.rec = FaceRecAPI.FaceRecognition(models)
        self.rec.load_files()

    def startrecognition(self):

        try:
            if self.facerecognition_thread.isAlive():
                return True
            else:
                self.rec = FaceRecAPI.FaceRecognition(models)
                self.rec.load_files()
                self.stream_thread = StreamThread()
                self.arduino_thread = ArduinoThread()
                self.process_pool = ThreadPool(processes=1)
                self.access_pool = ThreadPool(processes=1)
                self.facerecognition_thread = FaceRecognitionThread()
                self.facerecognition_thread.start()
                return False
        except AttributeError:
            self.stream_thread = StreamThread()
            self.arduino_thread = ArduinoThread()
            self.process_pool = ThreadPool(processes=1)
            self.access_pool = ThreadPool(processes=1)
            self.facerecognition_thread = FaceRecognitionThread()
            self.facerecognition_thread.start()
            return False


rec_threads = RecognitionThreads()


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
        super(ArduinoThread, self).__init__(target=rec_threads.rec.arduino_server, args=(arduino_lock,), name="ArduinoThread")
        self._stop_event = threading.Event()

    def destop(self):
        self._stop_event.clear()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class StreamThread(threading.Thread):
    def __init__(self):
        super(StreamThread, self).__init__(target=rec_threads.rec.read_stream, name="StreamThread")
        self._stop_event = threading.Event()

    def destop(self):
        self._stop_event.clear()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

restarted = False
stopped = False

def facerecognition():
    print("face recognition is starting up")
    try:
        rec_threads.rec.cap
    except AttributeError:
        rec_threads.rec.grab_cap()

    rec_threads.stream_thread.start()
    rec_threads.arduino_thread.start()
    print("Face Recognition is running")
    while True:
        if rec_threads.facerecognition_thread.stopped():
            rec_threads.arduino_thread.stop()
            rec_threads.stream_thread.stop()
            rec_threads.process_pool.terminate()
            rec_threads.access_pool.terminate()
            frameQ.task_done()
            rec_threads.arduino_thread.join()
            rec_threads.stream_thread.join()
            rec_threads.process_pool.join()
            rec_threads.access_pool.join()
            rec_threads.rec.arduino_server_pool.terminate()
            rec_threads.rec.arduino_server_pool.join()
            global restarted
            restarted = True
            global stopped
            stopped = True
            break
        process = rec_threads.process_pool.apply_async(rec_threads.rec.process)
        labels, frame = process.get()
        access = rec_threads.access_pool.apply_async(rec_threads.rec.access, args=(labels, frame, arduino_lock))
        if restarted == False:
            cv2.imshow("test", frame)
            cv2.waitKey(1)
        if frameQ.full():
            continue
        frameQ.put(frame)

    rec_threads.arduino_thread.destop()
    rec_threads.stream_thread.destop()
    rec_threads.facerecognition_thread.destop()
    rec_threads.rec.cap.release()
    cv2.destroyAllWindows()
    return


def stream_server():
    while True:
        image = frameQ.get()
        ret, jpeg = cv2.imencode('.jpg', image)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@login_required(login_url='/accounts/login')
def stream(request):
    try:
        rec_threads.startrecognition()
        return StreamingHttpResponse(streaming_content=stream_server(), content_type="multipart/x-mixed-replace;boundary=frame")
    except HttpResponseServerError:
        print("aborted")


@login_required(login_url='/accounts/login')
def index(request):
    try:
        running = rec_threads.facerecognition_thread.isAlive()
    except AttributeError:
        running = False
    subscription = frviews.subscription
    return HttpResponse(render(request, 'LiveView/LiveView.html', {'running': running, 'subscription': subscription}))


@login_required(login_url='/accounts/login')
def startAdmin(request):
    if rec_threads.startrecognition():
        message = "Face recognition is already running."
    else:
        message = "Face recognition has been started"
    admin.ModelAdmin.message_user(admin.ModelAdmin, request, message)
    return HttpResponseRedirect("../admin")


@login_required(login_url='/accounts/login')
def start(request):
    if rec_threads.startrecognition():
        message = "Face recognition is already running."
    else:
        message = "Face recognition has been started!"
    try:
        running = rec_threads.facerecognition_thread.isAlive()
    except AttributeError:
        running = False
    subscription = frviews.subscription
    return HttpResponse(render(request, 'LiveView/LiveView.html', {'message': message, 'running': running, 'subscription': subscription}))


@login_required(login_url='/accounts/login')
def stopAdmin(request):
    global stopped
    try:
        if rec_threads.facerecognition_thread.isAlive():
            rec_threads.facerecognition_thread.stop()
            stop_time = time.time()
            while time.time() - stop_time < 15:
                if stopped:
                    print("all killed")
                    message = "Face recognition has been stopped"
                    admin.ModelAdmin.message_user(admin.ModelAdmin, request, message)
                    stopped = False
                    return HttpResponseRedirect("../admin")
                time.sleep(1)
            else:
                message = "Face recognition could not be stopped"
        else:
            message = "Face recognition is not running!"
    except AttributeError:
        message = "Face recognition is not running!"
    admin.ModelAdmin.message_user(admin.ModelAdmin, request, message)
    stopped = False
    return HttpResponseRedirect("../admin")


@login_required(login_url='/accounts/login')
def stop(request):
    global stopped
    try:
        if rec_threads.facerecognition_thread.isAlive():
            rec_threads.facerecognition_thread.stop()
            stop_time = time.time()
            while time.time() - stop_time < 15:
                if stopped:
                    message = "Face recognition has been stopped"
                    print("all killed")
                    admin.ModelAdmin.message_user(admin.ModelAdmin, request, message)
                    stopped = False
                    return HttpResponse(render(request, 'LiveView/LiveView.html', {'message': message}))
                time.sleep(1)
            else:
                message = "Face recognition could not be stopped"
        else:
            message = "Face recognition is not running!"
    except AttributeError:
        message = "Face recognition is not running!"
    stopped = False
    try:
        running = rec_threads.facerecognition_thread.isAlive()
    except AttributeError:
        running = False
    subscription = frviews.subscription
    return HttpResponse(render(request, 'LiveView/LiveView.html', {'message': message, 'running': running, 'subscription': subscription}))


@login_required(login_url='/accounts/login')
def openAdmin(request):
    try:
        if rec_threads.facerecognition_thread.isAlive():
            rec_threads.rec.arduino_open("manual", arduino_lock)
            message = "Gate opened!"
        else:
            message = "Face recognition is not running!"
            arduino_lock.clear()
            print("lock cleared")
    except AttributeError:
        message = "There's a problem with the Arduino, try to restart it!"
        arduino_lock.clear()
        print("lock cleared")
    admin.ModelAdmin.message_user(admin.ModelAdmin, request, message)
    return HttpResponseRedirect("../admin")


@login_required(login_url='/accounts/login')
def open(request):
    try:
        if rec_threads.facerecognition_thread.isAlive():
            rec_threads.rec.arduino_open("manual", arduino_lock)
            message = "Gate opened!"
        else:
            message = "Face recognition is not running!"
            arduino_lock.clear()
            print("lock cleared")
    except AttributeError:
        message = "There's a problem with the Arduino, try to restart it!"
        arduino_lock.clear()
        print("lock cleared")
    try:
        running = rec_threads.facerecognition_thread.isAlive()
    except AttributeError:
        running = False
    subscription = frviews.subscription
    return HttpResponse(render(request, 'LiveView/LiveView.html', {'message': message, 'running': running, 'subscription': subscription}))




