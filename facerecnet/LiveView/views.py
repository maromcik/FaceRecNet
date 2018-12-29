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
x = FaceRecAPI.FaceRecognition(models)
x.load_files()
stream_thread = threading.Thread(target=x.read_stream)
arduino_thread = threading.Thread(target=x.arduino_server)
process_pool = ThreadPool(processes=1)
access_pool = ThreadPool(processes=1)
stream_server_pool = ThreadPool(processes=1)
frameQ = Queue(maxsize=5)


def startrecognition():
    if facerecognition_thread.is_alive() is False:
        facerecognition_thread.start()


def facerecognition():
    print("face recognition is starting up")
    try:
        x.cap
    except AttributeError:
        x.grab_cap()

    if arduino_thread.is_alive() is False:
        arduino_thread.daemon = True
        arduino_thread.start()
    if stream_thread.is_alive() is False:
        stream_thread.daemon = True
        stream_thread.start()
    print("Face Recognition is running")
    while True:
        process = process_pool.apply_async(x.process)
        labels, frame = process.get()
        access = access_pool.apply_async(x.access, args=(labels, frame))
        cv2.imshow("live", frame)
        cv2.waitKey(1)
        if frameQ.full():
            continue
        frameQ.put(frame)

def stream_server():

    while True:
        image = frameQ.get()
        ret, jpeg = cv2.imencode('.jpg', image)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

facerecognition_thread = threading.Thread(target=facerecognition)


@login_required(login_url='/accounts/login')
def stream(request):
    try:
        if facerecognition_thread.isAlive() is False:
            facerecognition_thread.start()
        return StreamingHttpResponse(stream_server(), content_type="multipart/x-mixed-replace;boundary=frame")
    except HttpResponseServerError as e:
        print("aborted")


@login_required(login_url='/accounts/login')
def index(request):
    if facerecognition_thread.isAlive() is False:
        facerecognition_thread.start()
        message = "Face recognition has been started"
    else:
        message = "Face recognition is already running."
    admin.ModelAdmin.message_user(admin.ModelAdmin, request, message)
    return HttpResponseRedirect("../admin")
