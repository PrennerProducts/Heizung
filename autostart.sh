#!/bin/sh

screen -T xterm -dmS Heizung
screen -S Heizung -p0 -X stuff "cd /home/pi/Heizung Mischersteuerung/Heizung
python3 main.py
"
