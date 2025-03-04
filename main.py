#!/usr/bin/python3.7
#####################################################################################################
# Mischer Motor Steuerung
REGELINTERVALL = 5 # nur alle % Minuten, soll der Mischermotor angesteuert werden (6*5=30sec)
MAX_REGELDIFFERENZ = 10.0 # Nur maximal 10 Grad Regelabweichung werden beruecksichtigt, damit der Regler nicht zu agressiv regelt
HYSTERESE_VORLAUFTEMPERATUR = 0.5 # Temperaturbereich, innerhalb dem nicht nachgeregelt wird
STELLZEIT_PRO_KELVIN_TEMP_DIFF = 10.0 # Wie viele Sekunden soll der Mischermotor pro Kelvin Temperaturabweichung und Regelintervall anfgesteuert werden? alt 4
SOLL_VORLAUFTEMPERATUR_BEI_MINUS_10_GRAD = 36.0 #34
SOLL_VORLAUFTEMPERATUR_BEI_PLUS_10_GRAD = 25.0
####################################################################################################
# Solarpufferwaereme_in_Heizung
PUFFERINTERVALL = 10 # nur alle %f Minuten, soll der Dreiwegehahn angesteuert werden
PUFFERHYSTERESE =  5 # 7 Temperaturbereich, innerhalb dem nicht nachgeregelt wird alt 7

#####################################################################################################
# BoilerPumpe:
BOILERINTERVALL = 10 # nur alle %f Minuten sollte die Pumpe an oder aus geschalten werden
sollTempBoiler = 40 # Temperatur auf die der Warmwasserboiler aufgeheizt werden soll
BoilerHysterese = 2 # Hysterese

######################################################################################################
import os
import time
import datetime
import logging
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
hahnstatus_auf = None # Initialisierung des Dreiwegehahnstatus mit None da die letze stellung unbekannt ist

sleep(5) # Bevor die Regelschleife startet, sollten wir warten, bis Temperatursensor gelesen und Aussentemperatur vom Server abgefragt wurden.

logging.basicConfig(filename="heizung.log",filemode="a", level=logging.INFO,format="%(asctime)s %(message)s" )


#vorlaufpumpe_an()  # Vorlaufpumpe nun dauerhaft an

logging.info("Starte Heizungssteuerung while(True)")
# ASCI ART
print(" __  __      _              _   _      _                 ")
print("|  \/  | ___(_)_ __   ___  | | | | ___(_)_____ __   __ _ ")
print("| |\/| |/ _ \ | '_ \ / _ \ | |_| |/ _ \ |_  / '_ \ / _` |")
print("| |  | |  __/ | | | |  __/ |  _  |  __/ |/ /| | | | (_| |")
print("|_|  |_|\___|_|_| |_|\___| |_| |_|\___|_/___|_| |_|\__, |")
print("                                                   |___/ ")

while(True):
    tAussen = Wetter.aussentemperatur
    tIst = Temperatursensor.vorlauftemperatur
    tSoll = min(SOLL_VORLAUFTEMPERATUR_BEI_0_GRAD + (SOLL_VORLAUFTEMPERATUR_STEIGUNG * tAussen), TEMPERATUR_NOTABSCHALTUNG - 1.0) # Vorlauftemperatur darf maximal 1 Grad unterhalb der Notabschaltung sein.
    tDelta = tIst - tSoll
    tPuffer = Temperatursensor.puffertemperatur
    tBoiler = Temperatursensor.boilertemperatur


    #print("tAussen=%.1f" %tAussen, "tSoll=%.1f" %tSoll, "tIst=%.1f" %tIst, "tDelta=%+.1f" %tDelta, "Zyklus: {0:2d}/{1}".format(Schleifenzaehler%REGELINTERVALL+1, REGELINTERVALL), "Historie:", historieString, f"tPuffer={tPuffer}", f"tBoiler={tBoiler}", time.strftime('%H:%M', time.localtime()))
    print("tAussen=%.1f" %tAussen, "tSoll=%.1f" %tSoll, "tIst=%.1f" %tIst, "tDelta=%+.1f" %tDelta, "Zyklus: {0:2d}/{1}".format(Schleifenzaehler%REGELINTERVALL+1, REGELINTERVALL), "Historie:", historieString, "tPuffer=%.2f" %tPuffer, "tBoiler=%.2f" %tBoiler, time.strftime('%H:%M', time.localtime()))
    #logging.info(f"tAussen={tAussen} tSoll={tSoll} tIst={tIst} tDelta={tDelta} tPuffer={tPuffer} tBoiler={tBoiler}")
    mystring = '%s' %"tAussen=%.1f" %tAussen, "tSoll=%.1f" %tSoll, "tIst=%.1f" %tIst, "tDelta=%+.1f" %tDelta, "Zyklus: {0:2d}/{1}".format(Schleifenzaehler%REGELINTERVALL+1, REGELINTERVALL), "Historie:", historieString, "tPuffer=%.2f" %tPuffer, "tBoiler=%.2f" %tBoiler, time.strftime('%H:%M', time.localtime())
    logging.info(mystring)
    
    if Schleifenzaehler % REGELINTERVALL == 0: # Alle 5 Minuten soll nachgeregelt werden
        print("Regelintervall!")
        tDeltaRegel = max(-MAX_REGELDIFFERENZ, min(tDelta, MAX_REGELDIFFERENZ)) # tDelta auf Regelbereich begrenzen
        if tDeltaRegel > HYSTERESE_VORLAUFTEMPERATUR:
            stellzeit = tDeltaRegel * STELLZEIT_PRO_KELVIN_TEMP_DIFF
            mischerZu(stellzeit)
            print("Mischer {0:.1f} Sekunden zu.".format(stellzeit))
            logging.info("Mischer {0:.1f} Sekunden zu.".format(stellzeit))
        elif tDeltaRegel < -HYSTERESE_VORLAUFTEMPERATUR:
            stellzeit = -tDeltaRegel * STELLZEIT_PRO_KELVIN_TEMP_DIFF
            mischerAuf(stellzeit)
            print("Mischer {0:.1f} Sekunden auf.".format(stellzeit))
            logging.info("Mischer {0:.1f} Sekunden auf.".format(stellzeit))

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
    if tBoiler >= (sollTempBoiler):
        if Schleifenzaehler % REGELINTERVALL == 1:
            print("Boiler ist Warm Normaler Modus! Boilerpumpe ist aus!")
            logging.info("Boiler ist Warm Normaler Modus! Boilerpumpe ist aus!")
            boiler_pumpe_aus()
        if Schleifenzaehler % PUFFERINTERVALL == 0: # alle PUFFERINTERWALL sekunden soll die Puffertemperatur kontrolliert werden und ggf der Dreiwegehahn geschalten werden.
            if tPuffer >= (tSoll + PUFFERHYSTERESE):
                if hahnstatus_auf == True:
                    print("Dreiwegehahn ist bereits auf.")
                    logging.info("Dreiwegehahn ist bereits auf.")
                else:
                    dreiWegeAuf(hahnzeit)
                    hahnstatus_auf = True
                    print("Dreiwegehahn %.2f Sekunden auf" %hahnzeit)
                    logging.info("Dreiwegehahn %.2f Sekunden auf" %hahnzeit)

            else:
                if hahnstatus_auf == True or hahnstatus_auf == None:
                    dreiWegeZu(hahnzeit)
                    hahnstatus_auf = False
                    print("Dreiwegehahn %.2f Sekunden zu" %hahnzeit)
                    logging.info("Dreiwegehahn %.2f Sekunden zu" %hahnzeit)

                else:
                    hahnstatus_auf = False
                    print("Dreiwege ist bereits zu.")
                    logging.info("Dreiwege ist bereits zu.")
            # Oelbrenner Relais An/Aus
            if hahnstatus_auf == True:
                oelbrenner_aus()        # Wenn Waerme aus dem Puffer genutz wird, dann Oelbrenner AUS!
                print("Oelbrenner ist AUS!")
                logging.info("Oelbrenner ist AUS!")

            elif hahnstatus_auf == False:
                oelbrenner_an()         # Wenn Waerme NICHT aus dem Puffer genutz wird, dann Oelbrenner AN!
                print("Oelbrenner ist AN")
                logging.info("Oelbrenner ist AN")
               
    if Schleifenzaehler % BOILERINTERVALL == 0: # alle BEULERINTERVALL sekunden soll die Boilerpumpe kontrolliert werden und ggf An- oder Ausgeschaltet werden.
        print("Boilerintervall kontrolliere Boilertemp=%.2f" %tBoiler)
        logging.info("Boilerintervall kontrolliere Boilertemp=%.2f" %tBoiler)
        if tBoiler < (sollTempBoiler):
            sollTempBoiler = 42
            print("sollTempBoiler = 42")
            if hahnstatus_auf == None:
                boiler_pumpe_an()
                dreiWegeZu(hahnzeit)
                hahnstatus_auf = False
                oelbrenner_an()
                print("Boilerpume ist an")
                print("Dreiwegehahn %.2f Sekunden zu" %hahnzeit)
                print("Ölbrenner ist an!")
                logging.info("Boilerpume ist an")
                logging.info("Dreiwegehahn %.2f Sekunden zu" %hahnzeit)
                logging.info("Boilerpume ist an")
            if hahnstatus_auf == False:
                boiler_pumpe_an()
                oelbrenner_an()
                hahnstatus_auf = False
                print("Boilerpume ist an")
                print("Dreiwegehahn ist zu")
                print("Ölbrenner ist an!")
                logging.info("Boilerpume ist an")
                logging.info("Dreiwegehahn ist zu")
                logging.info("Ölbrenner ist an!")
            if hahnstatus_auf == True:
                if (tPuffer) > (sollTempBoiler + 5):
                    boiler_pumpe_an()
                    print("Boilerpume ist an, heize Boiler mit SolarPuffer")
                    logging.info("Boilerpume ist an, heize Boiler mit SolarPuffer")

                else:
                    boiler_pumpe_aus()
                    print("ACHTUNG: Hahnstatus ist auf, aber Boiler ist kalt, Pumpe ist aus! KONTROLLE!!!!! ACHTUNG!!!!")
                    logging.warning("ACHTUNG: Hahnstatus ist auf, aber Boiler ist kalt, Pumpe ist aus! KONTROLLE!!!!! ACHTUNG!!!!")
        
        else:
            boiler_pumpe_aus()
            sollTempBoiler = 40
            print("Boiler ist warm, Pumpe ist aus")
            print("sollTempBoiler = 40")
            logging.info("Boiler ist warm, Pumpe ist aus")
    
    
    
    #Opsolete Notfalllösung zum heizen des Bilers im Fehlerfall
    # else:
    #     tempcount = 0
    #     sleeptime = 300
    #     while(True):
    #         tBoiler = Temperatursensor.boilertemperatur
    #         print("Boiler ist kalt, Boiler Modus! while(True)")
    #         vorlaufpumpe_an()
    #         print("Vorlaufpumpe ist an")
    #         if tempcount >= 12:
    #             break
    #         elif  tPuffer <= sollTempBoiler:
    #             if hahnstatus_auf == True or hahnstatus_auf == None:
    #                 dreiWegeZu(hahnzeit)
    #                 hahnstatus_auf = False
    #                 print("Dreiwegehahn %.2f Sekunden zu" %hahnzeit)
    #             print("Puffer ist kalt, heize mit ÖL") 
    #              # Oelbrenner Relais An/Aus
    #             oelbrenner_an()
    #             print("Oelbrenner ist AN")
    #             sleep(sleeptime)
    #             tempcount +=1
    #             print("10 Min heizen mit oel, neue Temperatur: tBoiler=%.2f" %tBoiler)
    #             print("tAussen=%.1f" %tAussen, "tSoll=%.1f" %tSoll, "tIst=%.1f" %tIst, "tDelta=%+.1f" %tDelta, "Zyklus: {0:2d}/{1}".format(Schleifenzaehler%REGELINTERVALL+1, REGELINTERVALL), "Historie:", historieString, "tPuffer=%.2f" %tPuffer, "tBoiler=%.2f" %tBoiler, time.strftime('%H:%M', time.localtime()))
    #         elif tPuffer > 45 and hahnstatus_auf == False or tPuffer > 46 and hahnstatus_auf == None:
    #             dreiWegeAuf(hahnzeit)
    #             hahnstatus_auf = True
    #             print("Dreiwegehahn %.2f Sekunden AUF" %hahnzeit)
    #             oelbrenner_aus()
    #             print('Oelbrenner aus !!!!')
    #             sleep(sleeptime)
    #             tempcount +=1
    #             print("10 Min heizen mit Solar, neue Temperatur: tBoiler=%.2f" %tBoiler)
    #             print("tAussen=%.1f" %tAussen, "tSoll=%.1f" %tSoll, "tIst=%.1f" %tIst, "tDelta=%+.1f" %tDelta, "Zyklus: {0:2d}/{1}".format(Schleifenzaehler%REGELINTERVALL+1, REGELINTERVALL), "Historie:", historieString, "tPuffer=%.2f" %tPuffer, "tBoiler=%.2f" %tBoiler, time.strftime('%H:%M', time.localtime()))
                
    #         elif tBoiler >= sollTempBoiler:
    #             break
            
    #         else:
    #             hahnstatus_auf = True
    #             print("Letz's heat the fucking Boiler!  tBoiler=%.2f tPuffer:%.2f" %tBoiler %tPuffer)
               

            

    Schleifenzaehler += 1
    sleep(60)

    # Check if RestartTime 5:00

    def time_in_range(start, end, current):
        """Returns whether current is in the range [start, end]"""
        return start <= current <= end

    start = datetime.time(5, 0, 0)
    end = datetime.time(5, 0, 45)
    current = datetime.datetime.now().time()


    if time_in_range(start, end, current):
        print("RebootTime: System Reboot NOW!")
        logging.warning("RebootTime: System reboot in 45 Seconds")
        break




os.system("sudo shutdown -r 40 ")
logging.critical("Reboot NOW")
