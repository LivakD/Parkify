import time, requests
from gpiozero import DistanceSensor
import RPi.GPIO as GPIO


class SonicSensor():
    
    def __init__(self, name, trigPin, echoPin):
        self.name = name
        self.trigPin = trigPin
        self.echoPin = echoPin
        self.sensor = DistanceSensor(echo=self.echoPin, trigger=self.trigPin, max_distance=3)
        self.belegt = False
        self.redLED = None
        self.greenLED = None
        self.neutralLED = None
        
        
    def addLED(self, LED):
        
        if "green" in LED.farbe.lower():
            self.greenLED = LED.pin
            print(f"Gruene LED an Pin {LED.pin} mit Sensor {self.name} verknuepft!")
            
        elif "red" in LED.farbe.lower():
            self.redLED = LED.pin
            print(f"Rote LED an Pin {LED.pin} mit Sensor {self.name} verknuepft!")
            
        else:
            self.neutralLED = LED.pin
            print(f"{LED.farbe}e LED an Pin {LED.pin} mit Sensor {self.name} verknuepft!")
            
            
    def pinSetup(self):
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.greenLED, GPIO.OUT)
        GPIO.setup(self.redLED, GPIO.OUT)
        GPIO.output(self.greenLED, GPIO.HIGH)
        GPIO.output(self.redLED, GPIO.LOW)
            
    
    def startParkScreening(self):
        
        #while True:
        distance = self.sensor.distance*100
        if self.belegt == True and distance < 9.8:
            print(f"{self.name} ist belegt.")
            commandPath =requests.get( f"http://[2001:7c0:2320:2:f816:3eff:fe82:34b2]:8000/Parkify/command?Parkplatznummer={self.name}&changeParkingLotStatus=belegt")
        else:
            self.belegt = False
            GPIO.output(self.redLED, GPIO.LOW)
            GPIO.output(self.greenLED, GPIO.HIGH)
            print(f"{self.name} ist frei! ({distance} cm)")
            commandPath =requests.get( f"http://[2001:7c0:2320:2:f816:3eff:fe82:34b2]:8000/Parkify/command?Parkplatznummer={self.name}&changeParkingLotStatus=frei")
            time.sleep(1)
                    
            if distance < 9.8:
                                              
                if self.belegt == False:
                    for x in range(5):
                        GPIO.output(self.greenLED, GPIO.LOW)
                        GPIO.output(self.redLED, GPIO.LOW)
                        time.sleep(0.2)
                        GPIO.output(self.greenLED, GPIO.HIGH)
                        GPIO.output(self.redLED, GPIO.HIGH)
                        time.sleep(0.2)
                        
                    
                    commandPath = requests.get(f"http://[2001:7c0:2320:2:f816:3eff:fe82:34b2]:8000/Parkify/command?Parkplatznummer={self.name}&changeParkingLotStatus=belegt")        
                    abfragePath =requests.get( f"http://[2001:7c0:2320:2:f816:3eff:fe82:34b2]:8000/Parkify/command?bookingStatus={self.name}")
                    status = abfragePath.text.strip().lower()
                    while status == "false" or status == "none":
                        if distance < 9.8:
                            GPIO.output(self.redLED, GPIO.HIGH)
                            GPIO.output(self.greenLED, GPIO.HIGH)
                            abfragePath =requests.get( f"http://[2001:7c0:2320:2:f816:3eff:fe82:34b2]:8000/Parkify/command?bookingStatus={self.name}")
                            status = abfragePath.text.strip().lower()
                            time.sleep(1)
                        else:
                            self.startParkScreening()
                        
                    self.belegt = True
                    GPIO.output(self.greenLED, GPIO.LOW)
                    GPIO.output(self.redLED, GPIO.HIGH)
                    print("Parkplatz gebucht!")
                    
                    
                        
                elif distance >= 9.8:
                    self.belegt = False
                    print(f"{self.name} ist wieder frei!")
                    commandPath = requests.get(f"http://[2001:7c0:2320:2:f816:3eff:fe82:34b2]:8000/Parkify/command?Parkplatznummer={self.name}&changeParkingLotStatus=frei")
                            
                

    GPIO.cleanup()
    
    
    
class LED():
    def __init__(self, farbe, pin):
        self.farbe = farbe
        self.pin = pin
        
        
Sensor1 = SonicSensor("Parkplatz 1", 13, 5)
Sensor2 = SonicSensor("Parkplatz 2", 23, 24)

LEDgreen = LED("green", 19)
LEDred = LED("red", 26)

LED2green = LED("green", 12)
LED2red = LED("red", 25)

Sensor1.addLED(LEDgreen)
Sensor1.addLED(LEDred)
Sensor1.pinSetup()

Sensor2.addLED(LED2green)
Sensor2.addLED(LED2red)
Sensor2.pinSetup()

print("Setup abgeschlossen, Parkscreening starten...")
while True:
    Sensor1.startParkScreening()
    Sensor2.startParkScreening()
    
            
            
            
            