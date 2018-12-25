from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.http import StreamingHttpResponse, HttpResponseServerError
from django.views.decorators.gzip import gzip_page
from django.views.decorators import gzip
import dlib
import cv2
import numpy as np
import time
import os
import threading
from queue import Queue
from multiprocessing.pool import ThreadPool
import multiprocessing
import pickle
import socket
from API import FaceRecAPI
from . models import Log, Person


stream = "rtsp://admin:M14ercedes1@192.168.1.64:554>/Streaming/Channels/101/?tcp"
stream2 = "rtsp://192.168.1.62/user=admin&password=&channel=1&stream=0.sdp?real_stream"
stream3 = "http://192.168.1.241:8080/video"
stream4 = "http://192.168.137.202:8080/video"
working_file = "/home/user/Documents/dlib/models/"
models = [working_file + "shape_predictor_5_face_landmarks.dat",
          working_file + "dlib_face_recognition_resnet_model_v1.dat",
          working_file + "shape_predictor_68_face_landmarks.dat"]
dir = "/home/user/PycharmProjects/resource/subjects"
rebs = "/home/user/PycharmProjects/resource/rebs2.mp4"

x = FaceRecAPI.FaceRecognition(models, dir, stream3, 0.25)
x.load_files()
stream_thread = threading.Thread(target=x.read_stream)
arduino_thread = threading.Thread(target=x.arduino_server)
process_pool = ThreadPool(processes=1)
access_pool = ThreadPool(processes=1)
stream_server_pool = ThreadPool(processes=1)
frameQ = Queue(maxsize=5)


def facerecognition():
    print("Face Recognition is running")
    if x.cap is None:
        x.grab_cap()
    if arduino_thread.isAlive() or stream_thread.isAlive():
        pass
    else:
        arduino_thread.daemon = True
        arduino_thread.start()
        stream_thread.daemon = True
        stream_thread.start()
    while True:
        process = process_pool.apply_async(x.process)
        labels, image = process.get()
        access = access_pool.apply_async(x.access, args=(labels,))
        cv2.imshow("live", image)
        cv2.waitKey(1)
        if frameQ.full():
            continue
        frameQ.put(image)

facerecognition_thread = threading.Thread(target=facerecognition)


def run_encodings(request):
    x.load_files()
    x.known_subjects_descriptors()
    x.load_files()
    message = "encoding done"
    return HttpResponse(render(request, 'LiveView/results.html', {"message": message}))

def load_files(request):
    x.load_files()
    message = "files have been loaded"
    return HttpResponse(render(request, 'LiveView/results.html', {"message": message}))

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
    return HttpResponse(render(request, 'LiveView/results.html', {"message": message}))
