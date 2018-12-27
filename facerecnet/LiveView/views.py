from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse, HttpResponseServerError
import cv2
import threading
from queue import Queue
from multiprocessing.pool import ThreadPool
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

x = FaceRecAPI.FaceRecognition(models, stream3, 0.25)
x.load_files()
stream_thread = threading.Thread(target=x.read_stream)
arduino_thread = threading.Thread(target=x.arduino_server)
process_pool = ThreadPool(processes=1)
access_pool = ThreadPool(processes=1)
stream_server_pool = ThreadPool(processes=1)
frameQ = Queue(maxsize=5)


def startrecognition():
    if arduino_thread.isAlive() is False:
        arduino_thread.daemon = True
        arduino_thread.start()
    if stream_thread.isAlive() is False:
        stream_thread.daemon = True
        stream_thread.start()


def facerecognition():
    print("face recognition is starting up")
    if x.cap is None:
        x.grab_cap()
    startrecognition()
    print("Face Recognition is running")
    while True:
        process = process_pool.apply_async(x.process)
        labels, image = process.get()
        access = access_pool.apply_async(x.access, args=(labels,image))
        cv2.imshow("live", image)
        cv2.waitKey(1)
        if frameQ.full():
            continue
        frameQ.put(image)

def stream_server():

    while True:
        image = frameQ.get()
        ret, jpeg = cv2.imencode('.jpg', image)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

facerecognition_thread = threading.Thread(target=facerecognition)


@login_required(login_url='/accounts/login')
def grab_cap(request):
    if facerecognition_thread.isAlive():
        x.grab_cap()
        startrecognition()
        message = "Video capture grabbed"
    else:
        message = "Face recognition is not running"
    return HttpResponse(render(request, 'LiveView/results.html', {"message": message}))


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
