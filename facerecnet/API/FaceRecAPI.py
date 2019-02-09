import dlib
import cv2
import numpy as np
import time
import os
import threading
from queue import Queue
from multiprocessing.pool import ThreadPool
import pickle
import socket
import string
import secrets
import select
import LiveView.models as database
from django.utils import timezone
from LiveView import views
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from webpush import send_user_notification
from facerecnet import views as frviews


class FaceRecognition:
    def __init__(self, models_paths):
        self.resize_factor = float(database.Setting.objects.get(pk=1).crop)
        self.device = database.Setting.objects.get(pk=1).device
        # self.device = "/home/user/PycharmProjects/resource/rebs2.mp4"
        self.models = models_paths
        self.dir = os.path.join(os.path.dirname(__file__), "..")

        self.frameQ = Queue()
        self.resize_lock = threading.Lock()

        self.descriptors = []
        self.names = []
        self.name = None
        self.ring_person = None
        self.authorized = []
        self.total_unknown = 0

        self.blink_frame_count = 0
        self.frame_count = 0

        self.auth_count = 0
        self.unknown_count = 0
        self.empty_count1 = 0
        self.empty_count2 = 0
        self.trigtime = 0

        self.detector = dlib.get_frontal_face_detector()
        self.predictor5 = dlib.shape_predictor(self.models[0])
        self.predictor68 = dlib.shape_predictor(self.models[2])
        self.facerec_model = dlib.face_recognition_model_v1(self.models[1])

        self.arduino_server_pool = ThreadPool(processes=1)
        # self.arduino_server_pool2 = ThreadPool(processes=1)

        self.host = ""
        self.port1 = 13081
        self.port2 = 13082

        self.ring = False

        self.persons = database.Person.objects.all()
        self.pks = list(self.persons.values_list('id', flat=True))
        print("primary keys have been loaded")
        self.names = list(self.persons.values_list('name', flat=True))
        print("names have been loaded")
        self.authorized_pks = list(self.persons.values_list('authorized', flat=True))
        print("authorization values have been loaded")
        self.files = list(self.persons.values_list('file', flat=True))
        print("images have been loaded")



    def draw(self, img, rect):
        (x, y, w, h) = rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)


    def PrintText(self, img, text, x, y):
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0), 2)


    def resize_img(self, img, fx=0.25, fy=0.25):
        return cv2.resize(img, (0, 0), fx=fx, fy=fy)


    def dlib2opencv(self, dlib_rect):
        x = dlib_rect.left()
        y = dlib_rect.top()
        w = dlib_rect.right()
        h = dlib_rect.bottom()
        return [x, y, w - x, h - y]


    def load_image(self, filename):
        img = cv2.imread(filename)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img


    def release_cap(self):
        self.cap.release()


    def grab_cap(self):
        self.resize_factor = float(database.Setting.objects.get(pk=1).crop)
        self.device = database.Setting.objects.get(pk=1).device
        # self.device = "/home/user/PycharmProjects/resource/rebs2.mp4"
        self.cap = cv2.VideoCapture(self.device)


    def load_files(self):
        self.device = database.Setting.objects.get(pk=1).device
        print("Device has been loaded")
        self.resize_factor = float(database.Setting.objects.get(pk=1).crop)
        print("crop factor has been loaded")
        self.persons = database.Person.objects.all()
        self.pks = list(self.persons.values_list('id', flat=True))
        print("primary keys have been loaded")
        self.names = list(self.persons.values_list('name', flat=True))
        print("names have been loaded")
        self.authorized_pks = list(self.persons.values_list('authorized', flat=True))
        print("authorization values have been loaded")
        self.files = list(self.persons.values_list('file', flat=True))
        print("images have been loaded")
        for name, authorized_pk in zip(self.names, self.authorized_pks):
            if authorized_pk:
                self.authorized.append(name)

        try:
            with open('descriptors.pkl', 'rb') as infile:
                self.descriptors = pickle.load(infile)
            print("descriptors have been loaded")
            infile.close()

        except FileNotFoundError:
            print("file descriptors.pkl not found")
            if input("Do you want to run the known people encoding? y/n: ").lower() == 'y':
                self.known_subjects_descriptors()
                with open('descriptors.pkl', 'rb') as infile:
                    self.descriptors = pickle.load(infile)
                print("descriptors have been loaded")
                infile.close()
            else:
                print("terminating")
                exit(101)

        return True

    def known_subjects_descriptors(self):
        descriptors = []
        self.dir = os.path.join(os.path.dirname(__file__), "..")
        for i in range(0, len(self.files)):
            full_path = self.dir + "/media/" + self.files[i]
            print("processing: ", full_path)
            img = self.load_image(full_path)
            face = self.detector(img, 1)
            if len(face) != 0:
                landmarks = self.predictor68(img, face[0])
                descriptors.append(np.array(self.facerec_model.compute_face_descriptor(img, landmarks)))
            else:
                print("No face in picture {}".format(full_path))
                database.Person.objects.filter(name=self.names[i]).delete()
                print("record deleted from database")

        with open('descriptors.pkl', 'wb') as outfile:
            pickle.dump(descriptors, outfile, pickle.HIGHEST_PROTOCOL)
        outfile.close()
        print("descriptors of known people has been saved")


    def detect(self, img):
        faces = self.detector(img, 1)
        if len(faces) != 0:
            return faces
        else:
            return None


    def find_landmarks(self, img, faces):
        landmarks = []
        for face in faces:
            landmarks.append(self.predictor68(img, face))
        return landmarks


    def descriptor(self, img, landmarks):
        return np.array(self.facerec_model.compute_face_descriptor(img, landmarks))


    def compare(self, known, unknown):
        return np.linalg.norm(known - unknown, axis=1)


    def read_stream(self):
        this_frame = True
        while True:
            if views.rec_threads.stream_thread.stopped():
                print("stream killed")
                self.frameQ.task_done()
                break
            ret, frame = self.cap.read()
            if frame is not None:
                if this_frame:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.frameQ.put(frame)
                this_frame = not this_frame
        return


    def process(self):
        labels = []
        image = self.frameQ.get()
        frame = self.resize_img(image, fx=self.resize_factor, fy=self.resize_factor)
        faces = self.detect(frame)
        if faces is not None:
            landmarks = self.find_landmarks(frame, faces)
            for y in range(0, len(faces)):
                rect = self.dlib2opencv(faces[y])
                self.draw(frame, rect)
                comparisons = (self.compare(self.descriptors, self.descriptor(frame, landmarks[y]))).tolist()

                for comparison in comparisons:
                    if comparison <= 0.55:
                        label = comparisons.index(comparison)
                        try:
                            self.PrintText(frame, self.names[label], rect[0], rect[1])
                        except IndexError:
                            print("Person does not exist anymore, you're most likely running encodings")
                        labels.append(self.blink_detector(landmarks[y], label))

                if all(i >= 0.55 for i in comparisons):
                    self.PrintText(frame, "unknown", rect[0], rect[1])
                    labels.append(None)


        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        # self.outputQ.put(frame)
        # cv2.imshow("SmartGate", image)
        # cv2.waitKey(1)
        return labels, frame


    def blink_detector(self, landmark, label):
        p1 = np.array([landmark.parts()[36].x, landmark.parts()[36].y])
        p2 = np.array([landmark.parts()[37].x, landmark.parts()[37].y])
        p3 = np.array([landmark.parts()[38].x, landmark.parts()[38].y])
        p4 = np.array([landmark.parts()[39].x, landmark.parts()[39].y])
        p5 = np.array([landmark.parts()[40].x, landmark.parts()[40].y])
        p6 = np.array([landmark.parts()[41].x, landmark.parts()[41].y])
        p2p6 = np.linalg.norm(p2-p6)
        p3p5 = np.linalg.norm(p3-p5)
        p1p4 = np.linalg.norm(p1-p4)
        # eye aspect ratio
        EAR = (p2p6 + p3p5) / (2 * p1p4)
        if EAR < 0.21:
            self.blink_frame_count += 1
        else:
            self.frame_count += 1

        if self.blink_frame_count >= 2 and self.frame_count >= 3:
            self.blink_frame_count = 0
            self.frame_count = 0
            return label, True
        else:
            return label, False



    def access(self, labels, image, lock):
        if not labels:
            self.empty_count1 += 1
            self.empty_count2 += 1
        else:
            for label in labels:
                if label is None:
                    self.unknown_count += 1
                    if (self.empty_count1 > 13) and self.unknown_count > 8 and self.ring is True:
                        print("unknown")
                        text = ''.join(secrets.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(20))
                        fullpath = self.dir+"/media/snapshots/"+text+".jpg"
                        djangopath = "snapshots/"+text+".jpg"
                        if cv2.imwrite(fullpath, image):
                            print("snap saved")
                        self.unknown_count = 0
                        self.empty_count1 = 0
                        log = database.Log.objects.create(person=None,time=timezone.now(), granted=False,
                                                          snapshot=djangopath)
                        log.save()
                        self.ring = False
                else:
                    if self.names[label[0]] in self.authorized:
                        if label[1] == True:
                            if time.time() - self.trigtime >= 2:
                                self.trigtime = time.time()
                                name = self.names[label[0]]
                                print("access granted for: ", name)
                                self.arduino_server_pool.apply_async(self.arduino_open, args=(name, lock,))
                    else:
                        self.auth_count += 1
                        if (self.empty_count2 > 10) and self.auth_count > 5:
                            self.empty_count2 = 0
                            self.auth_count = 0
                            name = self.names[label[0]]
                            print("access denied for: ", name)
                            person = database.Person.objects.get(name=name)
                            log = database.Log.objects.create(person=person, time=timezone.now(), granted=False, snapshot=None)
                            log.save()
                            for subscriber in database.Subscriber.objects.all():
                                if subscriber.subscription:
                                    user = subscriber.user
                                    print(subscriber.user)
                                    print(subscriber.subscription)
                                    payload = {'head': 'ring', 'body': name+' is here'}
                                    try:
                                        send_user_notification(user=user, payload=payload, ttl=1000)
                                    except TypeError:
                                        print("push typerror")
                                else:
                                    print("User not subscribed")



    def arduino_open(self, name, lock):
        command = "open"
        try:
            lock.set()
            print("lock set in open")
            self.c.send(command.encode("utf-8"))
            data = self.c.recv(8).decode("utf-8").strip("\r\n")
            data = data.rstrip()
            if data == "received" or data == "receive" or data == "d":
                if name != "manual":
                    person = database.Person.objects.get(name=name)
                    log = database.Log.objects.create(person=person, time=timezone.now(), granted=True,
                                                      snapshot=None)
                    log.save()
            print("from open: ", data)
            lock.clear()
            print("lock cleared")
        except (BrokenPipeError, ConnectionResetError, ConnectionError, ConnectionAbortedError, OSError):
            print("error")
            self.c.shutdown(2)
            self.c.close()
            self.s.shutdown(2)
            self.s.close()
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.host, self.port1))
            self.s.listen(1)
            self.c, addr = self.s.accept()
            print(addr, " reconnected")
            lock.clear()
            print("lock cleared")
        except socket.timeout:
            print("timed out on sending")
            self.c.send(command.encode("utf-8"))
            self.c.settimeout(10)
            data = self.c.recv(8).decode("utf-8").strip("\r\n")
            data = data.rstrip()
            if data == "received" or data == "receive" or data == "d":
                if name != "manual":
                    person = database.Person.objects.get(name=name)
                    log = database.Log.objects.create(person=person, time=timezone.now(), granted=True,
                                                      snapshot=None)
                    log.save()
            print("from open: ", data)
            lock.clear()
            print("lock cleared")

    def arduino_server(self, lock):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.host, self.port1))
        self.s.listen(1)
        self.c, addr = self.s.accept()
        print(addr, " connected")
        while True:
            if views.rec_threads.arduino_thread.stopped():
                self.c.shutdown(2)
                self.c.close()
                self.s.shutdown(2)
                self.s.close()
                print("arduino killed")
                break
            try:
                if lock.is_set():
                    time.sleep(0.5)
                    continue
                self.c.settimeout(10)
                data = self.c.recv(7).decode("utf-8")
                print("from server: ", data)
                if data.strip("\r\n") == "ringing":
                    self.ring = True
                    for subscriber in database.Subscriber.objects.all():
                        if subscriber.subscription:
                            user = subscriber.user
                            print(subscriber.user)
                            print(subscriber.subscription)
                            payload = {'head': 'ring', 'body': 'someone is ringing'}
                            try:
                                send_user_notification(user=user, payload=payload, ttl=1000)
                            except TypeError:
                                print("push typerror")
                        else:
                            print("no user")
            except (socket.timeout, OSError):
                continue
            time.sleep(1)






