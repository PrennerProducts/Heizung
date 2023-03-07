#!/usr/bin/python3.7
#####################################################################################################
# Mischer Motor Steuerung
REGELINTERVALL = 30 # nur alle % * Sleep(sekunden), soll der Mischermotor angesteuert werden (6*5=30sec)
MAX_REGELDIFFERENZ = 15.0 # Nur maximal 10 Grad Regelabweichung werden beruecksichtigt, damit der Regler nicht zu agressiv regelt
HYSTERESE_VORLAUFTEMPERATUR = 0.5 # Temperaturbereich, innerhalb dem nicht nachgeregelt wird
STELLZEIT_PRO_KELVIN_TEMP_DIFF = 10.0 # Wie viele Sekunden soll der Mischermotor pro Kelvin Temperaturabweichung und Regelintervall anfgesteuert werden? alt 4
SOLL_VORLAUFTEMPERATUR_BEI_MINUS_10_GRAD = 36.0 #34
SOLL_VORLAUFTEMPERATUR_BEI_PLUS_10_GRAD = 25.0
####################################################################################################
# Solarpufferwaereme_in_Heizung
PUFFERINTERVALL = 300 # nur alle %f Sekunden, soll der Dreiwegehahn angesteuert werden
PUFFERHYSTERESE =  7 # 7 Temperaturbereich, innerhalb dem nicht nachgeregelt wird alt 7

#####################################################################################################
# BoilerPumpe:
BOILERINTERVALL = 60 # nur alle %f Sekunden sollte die Pumpe an oder aus geschalten werden
sollTempBoiler = 43 # Temperatur auf die der Warmwasserboiler aufgeheizt werden soll
BoilerHysterese = 2 # Hysterese

######################################################################################################
import os
import time
import datetime
from time import sleep
from Solarpufferwaereme_in_Heizung import dreiWegeAuf, dreiWegeZu
import Temperatursensor
from Mischer import mischerAuf, mischerZu
import Wetter
from Notabschaltung import TEMPERATUR_NOTABSCHALTUNG
from Boiler_Aufheizungs_Pumpe import boiler_pumpe_an, boiler_pumpe_aus
from oelbrenner import oelbrenner_an, oelbrenner_aus, vorlaufpumpe_an, vorlaufpumpe_aus
#####################################################################################################

SOLL_VORLAUFTEMPERATUR_BEI_0_GRAD = (SOLL_VORLAUFTEMPERATUR_BEI_MINUS_10_GRAD + SOLL_VORLAUFTEMPERATUR_BEI_PLUS_10_GRAD) / 2.0
SOLL_VORLAUFTEMPERATUR_STEIGUNG = (SOLL_VORLAUFTEMPERATUR_BEI_PLUS_10_GRAD - SOLL_VORLAUFTEMPERATUR_BEI_MINUS_10_GRAD) / 20.0    # negative Steigung

historie = []
historieString = ""

Schleifenzaehler = 0

hahnzeit = 125 # Sekunden die von Hahn bentoeigt werden, um die Stellung zu wechseln
hahnstatus_auf = None # Initialisierung des Dreiwegehahnstatus mit None

sleep(5) # Bevor die Regelschleife startet, sollten wir warten, bis Temperatursensor gelesen und Aussentemperatur vom Server abgefragt wurden.


#vorlaufpumpe_an()


while(True):
    tAussen = Wetter.aussentemperatur
    tIst = Temperatursensor.vorlauftemperatur
    tSoll = min(SOLL_VORLAUFTEMPERATUR_BEI_0_GRAD + (SOLL_VORLAUFTEMPERATUR_STEIGUNG * tAussen), TEMPERATUR_NOTABSCHALTUNG - 1.0) # Vorlauftemperatur darf maximal 1 Grad unterhalb der Notabschaltung sein.
    tDelta = tIst - tSoll
    tPuffer = Temperatursensor.puffertemperatur
    tBoiler = Temperatursensor.boilertemperatur


    #print("tAussen=%.1f" %tAussen, "tSoll=%.1f" %tSoll, "tIst=%.1f" %tIst, "tDelta=%+.1f" %tDelta, "Zyklus: {0:2d}/{1}".format(Schleifenzaehler%REGELINTERVALL+1, REGELINTERVALL), "Historie:", historieString, f"tPuffer={tPuffer}", f"tBoiler={tBoiler}", time.strftime('%H:%M', time.localtime()))
    print("tAussen=%.1f" %tAussen, "tSoll=%.1f" %tSoll, "tIst=%.1f" %tIst, "tDelta=%+.1f" %tDelta, "Zyklus: {0:2d}/{1}".format(Schleifenzaehler%REGELINTERVALL+1, REGELINTERVALL), "Historie:", historieString, "tPuffer=%.2f" %tPuffer, "tBoiler=%.2f" %tBoiler, time.strftime('%H:%M', time.localtime()))


    if Schleifenzaehler % REGELINTERVALL == 0: # Alle 30 Sekunden soll nachgeregelt werden
        tDeltaRegel = max(-MAX_REGELDIFFERENZ, min(tDelta, MAX_REGELDIFFERENZ)) # tDelta auf Regelbereich begrenzen
        if tDeltaRegel > HYSTERESE_VORLAUFTEMPERATUR:
            stellzeit = tDeltaRegel * STELLZEIT_PRO_KELVIN_TEMP_DIFF
            mischerZu(stellzeit)
            print("Mischer {0:.1f} Sekunden zu.".format(stellzeit))
        elif tDeltaRegel < -HYSTERESE_VORLAUFTEMPERATUR:
            stellzeit = -tDeltaRegel * STELLZEIT_PRO_KELVIN_TEMP_DIFF
            mischerAuf(stellzeit)
            print("Mischer {0:.1f} Sekunden auf.".format(stellzeit))

        # Historie
        historie.append(tIst - tSoll)
        if len(historie) > 5:
            del historie[0]
        historieString = ""
        for element in reversed(historie):
            if historieString:
                historieString += " "
            historieString += "{0:+.1f}".format(element)


    # Solarpufferwaerme_in_Heizung.py implementierung
    if tBoiler >= (sollTempBoiler- BoilerHysterese):
        if Schleifenzaehler % REGELINTERVALL == 1:
            print("Boiler ist Warm Normaler Modus")
        if Schleifenzaehler % PUFFERINTERVALL == 0: # alle PUFFERINTERWALL sekunden soll die Puffertemperatur kontrolliert werden und ggf der Dreiwegehahn geschalten werden.
            if tPuffer >= (tSoll + PUFFERHYSTERESE):
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

            #if Schleifenzaehler % BOILERINTERVALL == 0: # alle BEULERINTERVALL sekunden soll die Boilerpumpe kontrolliert werden und ggf An- oder Ausgeschaltet werden.
            if tBoiler < (sollTempBoiler):
                if hahnstatus_auf == False or hahnstatus_auf == None:
                    boiler_pumpe_an()
                    hahnstatus_auf = False
                    print("Boilerpume ist an")
                if hahnstatus_auf == True:
                    if (tPuffer) > (sollTempBoiler + 10) or (tPuffer > tBoiler +10) :
                        boiler_pumpe_an()
                        print("Boilerpume ist an")

                    else:
                        boiler_pumpe_aus()
                        
                        print("Boiler nicht Warm aber trotzdem Boilerpumpe aus")
            elif hahnstatus_auf == True:
                if tPuffer > (tBoiler + BoilerHysterese+15):
                    boiler_pumpe_an()
                    print("Boiler hat sollTemp erreicht, Puffer ist aber waermer also Pumpe an!")
            else:
                boiler_pumpe_aus()
                print("Boiler ist warm, Pumpe ist aus")
    else:
        tempcount = 0
        while(1):
            tBoiler = Temperatursensor.boilertemperatur
            print("Boiler ist kalt, Boiler Modus! while(1)")
            #vorlaufpumpe_aus()
            if  tPuffer <= 45:
                dreiWegeZu(hahnzeit)
                hahnstatus_auf = False
                print("Puffer ist kalt, heize mit ÖL")
                print("Dreiwegehahn %.2f Sekunden zu" %hahnzeit)
                 # Oelbrenner Relais An/Aus
                oelbrenner_an()
                print("Oelbrenner ist AN")
            elif tPuffer > 45 and hahnstatus_auf == False or tPuffer > 46 and hahnstatus_auf == None:
                dreiWegeAuf(hahnzeit)
                hahnstatus_auf = True
                print("Dreiwegehahn %.2f Sekunden AUF" %hahnzeit)
                oelbrenner_aus()
                print('Oelbrenner aus !!!!')
            else:
                hahnstatus_auf = True
                print("Letz's heat the fucking Boiler!  tBoiler=%.2f with SOlar" %tBoiler)
               

            if tBoiler == sollTempBoiler:
                break
            tempcount +=1
            sleep(60)
            if tempcount == 10:
                break

    Schleifenzaehler = Schleifenzaehler + 1
    sleep(30)

    # Check if RestartTime 5:00

    def time_in_range(start, end, current):
        """Returns whether current is in the range [start, end]"""
        return start <= current <= end

    start = datetime.time(5, 0, 0)
    end = datetime.time(5, 0, 45)
    current = datetime.datetime.now().time()


    if time_in_range(start, end, current):
        print("RebootTime: System Reboot NOW!")
        break




os.system("sudo shutdown -r 0 ")
