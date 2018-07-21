import RPi.GPIO as GPIO
import firebase
import json
import time

PREV_STATION = 1
MY_STATION_ID = 2
NUM_PLATFORMS = 2

BLUE = 4
GREEN = 17
RED = 27

GREEN2 = 23
RED2 = 24
BLUE2 = 25

RED_THRESHOLD = 3
GREEN_THRESHOLD = 1
YELLOW_THRESHOLD = 2


def turnOn(colorNum):
    GPIO.setwarnings(False)
    GPIO.output(colorNum, False)

def turnOff(colorNum):
    GPIO.setwarnings(False)
    GPIO.output(colorNum, True)

def setUpPins():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    colorList = [GREEN, GREEN2, RED, RED2, BLUE, BLUE2]
    for color in colorList:
        GPIO.setup(color, GPIO.OUT)

def turnOffAll():
    colorList = [GREEN, GREEN2, RED, RED2, BLUE, BLUE2]
    for color in colorList:
        turnOff(color)

def turnOnWithCertainNum(platform, numPassengers):
    if platform == 0:
        turnOn(GREEN)
        if numPassengers >= RED_THRESHOLD:
            turnOff(GREEN)
            turnOn(RED)
        elif numPassengers >= YELLOW_THRESHOLD:
            turnOn(RED)
    elif platform == 1:
        turnOn(GREEN2)
        if numPassengers >= RED_THRESHOLD:
            turnOff(GREEN2)
            turnOn(RED2)
        elif numPassengers >= YELLOW_THRESHOLD:
            turnOn(RED2)


def get_most_recent_cars():
    cars = {}
    all_history = firebase.get('/history', None)

    # Get all from prev_station, group by car_id and then get the most recent timestamp for each car

    for key, value in all_history.items():
        if value["station_id"] == PREV_STATION:
            try:
                if cars[value["car_id"]] and cars[value["car_id"]]["timestamp"] < value["timestamp"]:
                    # Same car_id but newer data
                    cars[value["car_id"]] = value
            except:
                cars[value["car_id"]] = value

    for key, value in cars.items():
        print (key, value)

    return cars

if __name__ == '__main__':
    firebase = firebase.FirebaseApplication('https://metronome-nyc.firebaseio.com', None)
    setUpPins()
    cars = get_most_recent_cars()

    for platform_num in range(NUM_PLATFORMS):
        num_people_detected = cars[platform_num]["how_full"]
        turnOnWithCertainNum(platform_num, num_people_detected)
    
    time.sleep(2)
    turnOffAll()
