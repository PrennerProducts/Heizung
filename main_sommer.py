#####################################################################################################
# Mischer Motor Steuerung
REGELINTERVALL = 10 # nur alle % * Sleep(sekunden), soll der Mischermotor angesteuert werden (6*5=30sec)
MAX_REGELDIFFERENZ = 15.0 # Nur maximal 10 Grad Regelabweichung werden beruecksichtigt, damit der Regler nicht zu agressiv regelt
HYSTERESE_VORLAUFTEMPERATUR = 0.8 # Temperaturbereich, innerhalb dem nicht nachgeregelt wird
STELLZEIT_PRO_KELVIN_TEMP_DIFF = 4.0 # Wie viele Sekunden soll der Mischermotor pro Kelvin Temperaturabweichung und Regelintervall angesteuert werden?
SOLL_VORLAUFTEMPERATUR_BEI_MINUS_10_GRAD = 34.0
SOLL_VORLAUFTEMPERATUR_BEI_PLUS_10_GRAD = 25.0 

####################################################################################################
# Solarpufferwaereme_in_Heizung
PUFFERINTERVALL = 300 # nur alle %f Sekunden, soll der Dreiwegehahn angesteuert werden
PUFFERHYSTERESE = 6 # Temperaturbereich, innerhalb dem nicht nachgeregelt wird alt 7

#####################################################################################################
# BoilerPumpe:
BOILERINTERVALL = 60 # nur alle %f Sekunden sollte die Pumpe an oder aus geschalten werden
sollTempBoiler = 42 # Temperatur auf die der Warmwasserboiler aufgeheizt werden soll
BoilerHysterese = 2 # Hysterese 

######################################################################################################
import time
from time import sleep
from Solarpufferwaereme_in_Heizung import dreiWegeAuf, dreiWegeZu
import Temperatursensor
from Mischer import mischerAuf, mischerZu
import Wetter
from Notabschaltung import TEMPERATUR_NOTABSCHALTUNG
from Boiler_Aufheizungs_Pumpe import boiler_pumpe_an, boiler_pumpe_aus
from oelbrenner import oelbrenner_an, oelbrenner_aus
#####################################################################################################

SOLL_VORLAUFTEMPERATUR_BEI_0_GRAD = (SOLL_VORLAUFTEMPERATUR_BEI_MINUS_10_GRAD + SOLL_VORLAUFTEMPERATUR_BEI_PLUS_10_GRAD) / 2.0
SOLL_VORLAUFTEMPERATUR_STEIGUNG = (SOLL_VORLAUFTEMPERATUR_BEI_PLUS_10_GRAD - SOLL_VORLAUFTEMPERATUR_BEI_MINUS_10_GRAD) / 20.0    # negative Steigung

historie = []
historieString = ""

Schleifenzaehler = 0
 
hahnzeit = 125 # Sekunden die von Hahn bentoeigt werden, um die Stellung zu wechseln
hahnstatus_auf = None # Initialisierung des Dreiwegehahnstatus mit None

sleep(5) # Bevor die Regelschleife startet, sollten wir warten, bis Temperatursensor gelesen und Aussentemperatur vom Server abgefragt wurden.

while(True):
    
    tPuffer = Temperatursensor.puffertemperatur
    tBoiler = Temperatursensor.boilertemperatur

    

    # Solarpufferwaerme_in_Heizung.py implementierung
     
    if Schleifenzaehler % PUFFERINTERVALL == 0: # alle PUFFERINTERWALL sekunden soll die Puffertemperatur kontrolliert werden und ggf der Dreiwegehahn geschalten werden.
        if tPuffer >= (tBoiler + PUFFERHYSTERESE):
            if hahnstatus_auf == True:
                print("Dreiwegehahn ist bereits auf.")
                
                
            else:
                dreiWegeAuf(hahnzeit)
                hahnstatus_auf = True
                print("Dreiwegehahn %.2f Sekunden auf" %hahnzeit)
                
        else:
            if hahnstatus_auf == True or hahnstatus_auf == None:
                dreiWegeZu(hahnzeit)
                hahnstatus_auf = False
                print("Dreiwegehahn %.2f Sekunden zu" %hahnzeit)
                
            else:
                hahnstatus_auf = False
                print("Dreiwege ist bereits zu.")
        # Oelbrenner Relais An/Aus
        if hahnstatus_auf == True:
            oelbrenner_aus()        # Wenn Waerme aus dem Puffer genutz wird, dann Oelbrenner AUS!
            print("Oelbrenner ist AUS!")
            
        elif hahnstatus_auf == False:
            oelbrenner_an()         # Wenn Waerme NICHT aus dem Puffer genutz wird, dann Oelbrenner AN!
            print("Oelbrenner ist AN")

        if Schleifenzaehler % BOILERINTERVALL == 0: # alle BEULERINTERVALL sekunden soll die Boilerpumpe kontrolliert werden und ggf An- oder Ausgeschaltet werden.
            if tBoiler < (sollTempBoiler - BoilerHysterese):
                if hahnstatus_auf == False:
                    boiler_pumpe_an()
                    print("Boilerpume ist an")
                if hahnstatus_auf == True:
                    if (tPuffer) > ( tBoiler- BoilerHysterese):
                        boiler_pumpe_an()
                        print("Boilerpume ist an")

                    else:
                        boiler_pumpe_aus()
                        print("Boiler nicht Warm aber trotzdem Boilerpumpe aus")
            elif hahnstatus_auf == True:
                if tPuffer > (tBoiler + BoilerHysterese) and tPuffer < 60:
                    boiler_pumpe_an()
                    print("Boiler hat sollTemp erreicht, Puffer ist aber waermer also Pumpe an!")
            else:
                boiler_pumpe_aus()
                oelbrenner_aus()
                print("Boiler ist warm, Pumpe ist aus, oelbrenner aus!")
    
    Schleifenzaehler = Schleifenzaehler + 1
    print("Boiler Temperatur = ", tBoiler,time.strftime('%H:%M', time.localtime()))
    print("Buffer Temperatur = ",tPuffer)
    sleep(30)