import argparse
import picamera
import pyaudio
import time
import wave
import StringIO
from picotts import PicoTTS
from google.cloud import vision
from google.cloud.vision import types
from PIL import Image, ImageDraw
from firebase import firebase
from socketIO_client import SocketIO, LoggingNamespace

firebase = firebase.FirebaseApplication('https://metronome-nyc.firebaseio.com', None)
camera = picamera.PiCamera()
picotts = PicoTTS()

SERVER = 'api.memeboard.net'
PORT = 80
TRAIN_ID = 10011
CAR_ID = 0

STATION_LIST = [0,1,2,3]

station_index = 1

def playSound():
    global picotts
    wavs = picotts.synth_wav('Stand clear of the closing doors please.');
    wav = wave.open(StringIO.StringIO(wavs))
    p = pyaudio.PyAudio()  
    stream = p.open(format = p.get_format_from_width(wav.getsampwidth()),  
                    channels = wav.getnchannels(),  
                    rate = wav.getframerate(),  
                    output = True)  
    data = wav.readframes(1024)  

    while data:  
        stream.write(data)  
        data = wav.readframes(1024)  

    stream.stop_stream()  
    stream.close()  

    p.terminate()  


def takephoto():
    camera.capture('image.jpg')

def detect_face(face_file, max_results=4):
    client = vision.ImageAnnotatorClient()

    content = face_file.read()
    image = types.Image(content=content)

    return client.face_detection(image=image).face_annotations


def highlight_faces(image, faces, output_filename):
    im = Image.open(image)
    draw = ImageDraw.Draw(im)

    for face in faces:
        box = [(vertex.x, vertex.y)
               for vertex in face.bounding_poly.vertices]
        draw.line(box + [box[0]], width=5, fill='#00ff00')

    im.save(output_filename)
    
def on_connect():
    print('Connected')

def on_disconnect():
    print('Disconnected')

def on_reconnect():
    print('Reconnected')

def on_triggerCamera(*args):
    print(args)
    global station_index
    print('Detecting train riders...')
    takephoto()
    with open('image.jpg', 'rb') as image:
        playSound()
        faces = detect_face(image, 50)
        print('Found {} face{}'.format(
            len(faces), '' if len(faces) == 1 else 's'))

        print('Writing to file {}'.format('output.jpg'))

        image.seek(0)
        # highlight_faces(image, faces, 'output.jpg')
        train_car = {
                'timestamp' : time.time(),
                'train_id' : TRAIN_ID,
                'car_id' : CAR_ID,
                'how_full' : len(faces),
                'station_id' : STATION_LIST[station_index]
        }

        result = firebase.post('/history', train_car)
        print result
        # station_index = (station_index + 1) % 4
        print('Moving to station ' + str(station_index))
        socketIO.emit('update_ui')
        print('Emitted update_ui')

print('Client is running, listening for commands')
socketIO = SocketIO(SERVER, PORT, LoggingNamespace)
socketIO.on('connect', on_connect)
socketIO.on('disconnect', on_disconnect)
socketIO.on('reconnect', on_reconnect)
socketIO.on('trigger_camera', on_triggerCamera)
socketIO.wait(seconds=10000)

