"""Dieses Skript regelt den Oelbrenner, wenn der Solarpuffer warm genug ist wird der oelbrenner ausgeschalten."""

OELBRENNER_PIN = 37                   # Pin fuer das Relais, das den Oelbrenner schaltet


import atexit
import threading
from time import sleep
import RPi.GPIO as GPIO

#GPIO.setwarnings(False)               # keine Warnung, wenn die GPIOs beim letzen mal nicht aufgeraeumt wurden
GPIO.setmode(GPIO.BOARD)              # RPi.GPIO Layout verwenden (wie Pin-Nummern)
GPIO.setup(OELBRENNER_PIN, GPIO.OUT)
atexit.register(GPIO.cleanup)



"""
Schaltet die Relais so, dass der Oelbrenner Haubtschalter an ist. Ob der Brenner aufheitzen muss wird hier nicht gesteuert sonder über den Brenner selbst.
Die Funktion darft nur vom Oelbrenner Thread selbst benutzt werden. (Raise condition)
"""
def oelbrenner_an():
    GPIO.output(OELBRENNER_PIN, GPIO.LOW)  # Relais ist Low-Aktiv
    
def oelbrenner_aus():
    GPIO.output(OELBRENNER_PIN, GPIO.HIGH) # Relais ist Low-Aktiv!



