from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
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
# x.known_subjects_descriptors()
x.load_files()
e = threading.Event()
stream_thread = threading.Thread(target=x.read_stream)
arduino_thread = threading.Thread(target=x.arduino_server)
process_pool = ThreadPool(processes=1)
access_pool = ThreadPool(processes=1)
stream_server_pool = ThreadPool(processes=1)


def recognition():
    pass

FaceRecThread = threading.Thread(target=recognition)

def stream_server():
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
        # image = x.outputQ.get()
        cv2.imshow("live", image)
        cv2.waitKey(1)
        image = x.resize_img(image, fx=2, fy=2)
        ret, jpeg = cv2.imencode('.jpg', image)
        frame = jpeg.tobytes()
        yield(b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')



def runfacerec(request):
    if FaceRecThread.isAlive():
        return HttpResponse(render(request, 'LiveView/results.html'))
    else:
        FaceRecThread.start()
        return HttpResponse("Face Recognition has been started!")

# @gzip.gzip_page
def index(request):
    try:
        # stream_server()
        return StreamingHttpResponse(stream_server(), content_type="multipart/x-mixed-replace;boundary=frame")
    except HttpResponseServerError as e:
        print("aborted")
