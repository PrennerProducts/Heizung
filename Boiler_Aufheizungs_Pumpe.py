# In diesem Skrypt wird eine Pumpe gesteutert, die den Boiler entweder mit der Wärme aus
# der Öl-Heizung oder aus dem Solarpufferspeicher erhitzt.ArithmeticError()


BOILER_RELAIS_PIN_AN = 22           # Pin für die Boilerpumpe noch ABÄNDERN!!! neues Relay 

import atexit
import threading
from time import sleep
import RPi.GPIO as GPIO

#GPIO.setwarnings(False)               # keine Warnung, wenn die GPIOs beim letzen mal nicht aufgeraeumt wurden
GPIO.setmode(GPIO.BOARD)              # RPi.GPIO Layout verwenden (wie Pin-Nummern)
GPIO.setup(BOILER_RELAIS_PIN_AN, GPIO.OUT)
#atexit.register(GPIO.cleanup)

def boiler_pumpe_an():
    GPIO.output(BOILER_RELAIS_PIN_AN, GPIO.LOW)   # Relais ist Low-Aktiv
    
def boiler_pumpe_aus():
    GPIO.output(BOILER_RELAIS_PIN_AN, GPIO.HIGH) # Relais ist Low-Aktiv

    
    

"""class BoilerpumpenThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True # damit sich das Programm beenden kann, ohne dass der BoilerPumpen-Thread beendet werden muss
    def run(self):
        while True:
            if mischerSekundenZu:
                mischerSekundenZu = max(0, mischerSekundenZu - 0.1)
                relaisZu()
            elif mischerSekundenAuf:
                mischerSekundenAuf = max(0, mischerSekundenAuf - 0.1)
                relaisAuf()
            else:
                relaisNeutral()
                sleep(0.1)"""
# Boiler Thread wird automatisch beim Laden des Moduls gestartet
#boilerThread = BoilerpumpenThread()
#boilerThread.start()