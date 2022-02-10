

from time import sleep
from Solarpufferwaereme_in_Heizung import dreiWegeAuf, dreiWegeZu
import Temperatursensor
from Mischer import mischerAuf, mischerZu
import Wetter
from Notabschaltung import TEMPERATUR_NOTABSCHALTUNG
from Boiler_Aufheizungs_Pumpe import boiler_pumpe_an, boiler_pumpe_aus
from time import sleep




boiler_pumpe_an()
print("Boilerpume ist an")
mischerAuf(10)
print("Mischersec auf")
time.sleep(10)