"""Dieses Skript regelt einen 3-Wegehahn, dieser entscheidet ob Wäreme aus dem Solarpufferspeicher in den Heizkreislauf fließt"""

DREI_WEGE_RELAIS_AUF_PIN = 37                   # Pin fuer das Relais, das den Mischermotor in auf-Richtung ansteuert
DREI_WEGE_RELAIS_ZU_PIN = 38                    # Pin fuer das Relais, das den Mischermotor in zu-Richtung ansteuert

import atexit
import threading
from time import sleep
import RPi.GPIO as GPIO

#GPIO.setwarnings(False)               # keine Warnung, wenn die GPIOs beim letzen mal nicht aufgeraeumt wurden
GPIO.setmode(GPIO.BOARD)              # RPi.GPIO Layout verwenden (wie Pin-Nummern)
GPIO.setup(DREI_WEGE_RELAIS_AUF_PIN, GPIO.OUT)
GPIO.setup(DREI_WEGE_RELAIS_ZU_PIN, GPIO.OUT)
atexit.register(GPIO.cleanup)


dreiWegeSekundenAuf = 0              # interner Werte, der mit DreiWegeAuf() gesetzt werden kann
dreiwegeSekundenZu = 0              # interner Werte, der mit DreiWegeZu() gesetzt werden kann


"""
Signalisiet dem DreiWege Thread, dass der Dreiwegehahnmotor fuer die gegebene Anzahl Sekunden in richtung Auf drehen soll.
Allerdings nur unter der Vorraussetzung dass der Dreiwegehahn nicht gerade am Zu drehen ist.
"""
def dreiWegeAuf(sekunden):
    global dreiWegeSekundenAuf
    global dreiwegeSekundenZu
    if dreiwegeSekundenZu == 0:
        dreiWegeSekundenAuf = max(dreiWegeSekundenAuf, sekunden)

"""
Signalisiet dem DreiWege Thread, dass der Dreiwegehahnmotor fuer die gegebene Anzahl Sekunden in richtung Zu drehen soll.
Zudrehen hat aus Sicherheitsgruenden immer Vorrang vor Aufdrehen.
"""
def dreiWegeZu(sekunden):
    global dreiWegeSekundenAuf
    global dreiwegeSekundenZu
    dreiWegeSekundenAuf = 0
    dreiwegeSekundenZu = max(dreiwegeSekundenZu, sekunden)

"""
Schaltet die Relais so, dass der DreiwegeMotor in Richtung Auf dreht.
Die Funktion darft nur vom Dreiwege Thread selbst benutzt werden. (Raise condition)
"""
def dreiwegerelaisAuf():
    GPIO.output(DREI_WEGE_RELAIS_ZU_PIN, GPIO.HIGH)  # Relais ist Low-Aktiv
    sleep(0.1)                             # Warte kurze Zeit, damit Motor nicht zu schnell Richtung wechseln muss
    GPIO.output(DREI_WEGE_RELAIS_AUF_PIN, GPIO.LOW)  # Relais ist Low-Aktiv

"""
Schaltet die Relais so, dass der DreiwegeMotor in Richtung Zu dreht.
Die Funktion darft nur vom Dreiwege Thread selbst benutzt werden. (Raise condition)
"""
def dreiwegerelaisZu():
    GPIO.output(DREI_WEGE_RELAIS_AUF_PIN, GPIO.HIGH) # Relais ist Low-Aktiv
    sleep(0.1)                             # Warte kurze Zeit, damit Motor nicht zu schnell Richtung wechseln muss
    GPIO.output(DREI_WEGE_RELAIS_ZU_PIN, GPIO.LOW)   # Relais ist Low-Aktiv

"""
Schaltet die Relais so, dass der DreiwegeMotor stehen bleibt.
"""
def dreiwegerelaisNeutral():
    GPIO.output(DREI_WEGE_RELAIS_AUF_PIN, GPIO.HIGH) # Relais ist Low-Aktiv
    GPIO.output(DREI_WEGE_RELAIS_ZU_PIN, GPIO.HIGH)  # Relais ist Low-Aktiv


"""
Der Dreiwege Thread liest zyklisch die Sekundenwerte, die mit dreiWegeAuf() und dreiWegeZu() gesetzt wurden
und steuert entsprechend die Mischer Relais an.
"""
class DreiwegeThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True # damit sich das Programm beenden kann, ohne dass der Mischer-Thread beendet werden muss
    def run(self):
        global dreiWegeSekundenAuf
        global dreiwegeSekundenZu
        while True:
            if dreiwegeSekundenZu:
                dreiwegeSekundenZu = max(0, dreiwegeSekundenZu - 0.1)
                dreiwegerelaisZu()
            elif dreiWegeSekundenAuf:
                dreiWegeSekundenAuf = max(0, dreiWegeSekundenAuf - 0.1)
                dreiwegerelaisAuf()
            else:
                dreiwegerelaisNeutral()
                sleep(0.1)

# Mischer Thread wird automatisch beim Laden des Moduls gestartet
dreiwegeThread = DreiwegeThread()
dreiwegeThread.start()




