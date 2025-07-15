from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import os, json, csv, requests
from datetime import date, datetime, timedelta
import pytz
from django.core.files.storage import FileSystemStorage
from lxml import etree
import xml.etree.ElementTree as ET
import smtplib
from email.message import EmailMessage


tz = pytz.timezone("Europe/Berlin")




def Pruefung(request):
    accname = request.GET.get("accname", "")
    username = request.GET.get("username", "")
    pwd = request.GET.get("pwd", "")
    email = request.GET.get("email", "")
    plateCountry = request.GET.get("country", "")
    plateNumber = request.GET.get("numberplate", "")

    userPath = f"/var/www/django-project/Parkify/data/users/{accname}.json"


    if not os.path.isfile(userPath):

        emptTmpl = {
            "username": username,
            "pwd": pwd,
            "email": email,
            "status": "normal",
            "letzterLogIn": datetime.now(tz).strftime("%d.%m.%Y, %H:%M"),
            "anzahlMahnungen": 0,
            "anzahlAbschleppungen": 0,
            "ParkkarteVorhanden": False,
            "gesperrt": False,
            "fahrzeuge": [
                {
                    "Landerkennung": plateCountry,                
                    "Kennzeichen": plateNumber.upper(),
                    "Avatar": {
                        "name": "Limousine",
                        "topView": "http://[2001:7c0:2320:2:f816:3eff:fe82:34b2]/Parkify/WebPics/topView4.png",
                        "frontView": "http://[2001:7c0:2320:2:f816:3eff:fe82:34b2]/Parkify/WebPics/frontView4.png"
                    },
                    "Parkhistorie": []
                }
            ]
        }

        with open(userPath, "w", encoding="utf-8") as file:
            tmplDump = json.dumps(emptTmpl, indent = 2)
            file.write(tmplDump)
    
    
    with open(userPath, "r", encoding="utf-8") as file:
        userData = file.read()

    userData = json.loads(userData)  

    if userData["gesperrt"] == True:
        return HttpResponseRedirect("http://[2001:7c0:2320:2:f816:3eff:fe82:34b2]/Parkify/Wrong.html")

    else:
        if userData["pwd"] == pwd:

            if userData["status"] == "normal":
                return HttpResponseRedirect(f"/Parkify/Home?accname={accname}&pwd={pwd}")
            elif userData["status"] == "admin":
                return HttpResponseRedirect(f"/Parkify/Adminview?accname={accname}&pwd={pwd}")
        


        else:
            return HttpResponseRedirect("http://[2001:7c0:2320:2:f816:3eff:fe82:34b2]/Parkify/Wrong.html")



def userPageHome(request):
    accname = request.GET.get("accname", "")
    pwd = request.GET.get("pwd", "")
    parkdauer = request.GET.get("Parkdauer", "")
    accname = request.GET.get("accname", "")
    accname = request.GET.get("accname", "")
    parkplatzWahl = request.GET.get("P", "")
    autoAuswahl = request.GET.get("carSelection", "") #Kennzeichen wird übergeben
    parkpreisInEuro = request.GET.get("Parkpreis", "")

    class Avatar():
        def __init__(self, path):
            self.path = path
            self.cars = []

            self.load()
        
        def load(self):
            with open(self.path, "r") as file:
                carData = json.load(file)

            for car in carData:
                self.cars.append(car)
                    
        def returnChosenAvatarLinks(self, fromWho, plate):
            for item in fromWho.fahrzeuge:
                if plate in item["Kennzeichen"]:
                    for linkElement in self.cars:
                        if item["Avatar"] in linkElement["name"]:
                            avatarElement = linkElement

                            
            

        

    class SettingsdataSheet():
        def __init__(self, settingsPath):
            self.path = settingsPath
            self.stadt = ""
            self.parkraum = ""
            self.abschleppUnternehmen = ""
            self.parkPreisProMinute = ""
            self.hoechstParkDauerInH = 0
            self.toleranzInProzent = 0
            self.parkplaetze = []

            self.load()

        def load(self):
            with open(self.path, "r") as file:
                settingsData = json.load(file)

            self.stadt = settingsData["Stadt"]
            self.parkraum = settingsData["Parkraum"]
            self.abschleppUnternehmen = settingsData["KontaktAbschleppunternehmen"]
            self.parkPreisProMinute = settingsData["ParkPreisProMinute"]
            self.hoechstParkDauerInH = settingsData["HoechstparkdauerInH"]
            self.toleranzInProzent = settingsData["ToleranzInProzent"]
            self.parkplaetze = []
            for item in settingsData["Parkplaetze"]:
                self.parkplaetze.append(item)
        
        def save(self):
            saveData = {
                "Stadt": self.stadt,
                "Parkraum": self.parkraum,
                "KontaktAbschleppunternehmen": self.abschleppUnternehmen,
                "ParkPreisProMinute": self.parkPreisProMinute,
                "HoechstparkdauerInH": self.hoechstParkDauerInH,
                "ToleranzInProzent": self.toleranzInProzent,
                "Parkplaetze": self.parkplaetze
            }

            with open(self.path, "w") as file:
                file.write(json.dumps(saveData, indent = 3))

            

    class UserdataSheet():
        def __init__(self, userPath):
            self.path = userPath
            self.username = ""
            self.pwd = ""
            self.email = ""
            self.status = ""
            self.lastLogin = ""
            self.anzahlMahnungen = ""
            self.anzahlAbschleppungen = ""
            self.parkKarteVorhanden = ""
            self.gesperrt = ""
            self.fahrzeuge = []

            self.load()
            self.save()

        def load(self):
            with open(self.path, "r") as file:
                userData = json.load(file)
            
            self.username = userData["username"]
            self.pwd = userData["pwd"]
            self.email = userData["email"]
            self.status = userData["status"]
            self.lastLogin = userData["letzterLogIn"]
            self.anzahlMahnungen = userData["anzahlMahnungen"]
            self.anzahlAbschleppungen = userData["anzahlAbschleppungen"]
            self.parkKarteVorhanden = userData["ParkkarteVorhanden"]
            self.gesperrt = userData["gesperrt"]
            self.fahrzeuge = []
            for item in userData["fahrzeuge"]:
                self.fahrzeuge.append(item)
            
        def changeValue(self, valueToChange, newValue):
            setattr(self, valueToChange, newValue)

        def numberOfActiveParkings(self):
            parkings = 0
            for car in self.fahrzeuge:
                for entry in car["Parkhistorie"]:
                    if entry["Ende"] == 0:
                        parkings += 1
            
            return parkings

        
        def startParking(self, Kennzeichen, Parkplatz, Dauer, Preis, cityElement):
            for item in self.fahrzeuge:
                if Kennzeichen in item["Kennzeichen"]:
                    neueDauer = float(Dauer)
                    neueZeit = datetime.now(tz) + timedelta(minutes=neueDauer)
                    neuerEintrag = {
                        "Datum": str(datetime.now(tz).strftime("%d.%m.%Y, %H:%M")),
                        "Stadt": city.stadt,
                        "Parkraum": city.parkraum,
                        "Parkplatz": Parkplatz,
                        "GebuchteDauer": neueDauer,
                        "Start": str(datetime.now(tz).time().strftime("%H:%M:%S")),
                        "Ende": 0,
                        "GesamtpreisInEuro": Preis
                    }
                    item["Parkhistorie"].append(neuerEintrag)

                    self.save()
                    
                    for place in cityElement.parkplaetze:
                        if str(Parkplatz) in place["name"]:
                            place["belegt"] = True
                            newEntry = {                             
                                "Datum": str(datetime.now(tz).strftime("%d.%m.%Y, %H:%M")),
                                "Kennzeichen": Kennzeichen,
                                "Start": str(datetime.now(tz).time().strftime("%H:%M:%S")),
                                "Ende": str(neueZeit.strftime("%H:%M:%S"))
                            }
                            place["Parkverlauf"].append(newEntry)

                            cityElement.save()

        def emailsenden(self, betreff, inhalt):
            absender = "web.app.parkify@gmail.com"
            passwort = "nctktlekanowgzay"
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(absender, passwort)


            msg = EmailMessage()
            msg["From"] = absender
            msg["To"] = self.email
            msg["Subject"] = betreff
            msg.set_content(inhalt)

            server.send_message(msg)
            server.quit()



        def stopParkingAndCalculatePrice(self, Kennzeichen):
            for item in self.fahrzeuge:
                if Kennzeichen in item["Kennzeichen"]:
                    for entry in item["Parkhistorie"]:
                        if entry["Ende"] == 0:
                            entry["Ende"] = str(datetime.now(tz).time().strftime("%H:%M:%S"))
                            timeStart = datetime.strptime(entry["Start"], "%H:%M:%S")
                            timeEnd = datetime.strptime(entry["Ende"], "%H:%M:%S")
                            parkingTime = timeEnd - timeStart
                            Preis = int(round(parkingTime.total_seconds() / 60 * city.parkPreisProMinute, 2))

                            entry["GesamtpreisInEuro"] = Preis


                            mailtext = f"""\
                                Hallo {self.username},

                                Ihre Parkzeit ist beendet.

                                Fahrzeug: {Kennzeichen}
                                Parkplatz: {Parkplatz}
                                Startzeit: {Startzeit}
                                Endzeit: {entry['Ende']}
                                Kosten: {entry['GesamtpreisInEuro']} €

                                Vielen Dank für die Nutzung von Parkify!

                                Ihr Parkify-Team
                            """
                            self.emailsenden(self.email, "Ihre Parkrechnung", mailtext)


 
        def save(self):
            saveData = {
                "username": self.username,
                "pwd": self.pwd,
                "email": self.email,
                "status": self.status,
                "letzterLogIn": datetime.now(tz).strftime("%d.%m.%Y, %H:%M"),
                "anzahlMahnungen": self.anzahlMahnungen,
                "anzahlAbschleppungen": self.anzahlAbschleppungen,
                "ParkkarteVorhanden": self.parkKarteVorhanden,
                "gesperrt": self.gesperrt,
                "fahrzeuge": self.fahrzeuge
            }

            with open(self.path, "w") as file:
                file.write(json.dumps(saveData, indent = 3))

    #************************* Dateipfade *************************#
    carAvatarPath = "/var/www/django-project/Parkify/data/Bilder/Cars/cars.json"
    userPath = f"/var/www/django-project/Parkify/data/users/{accname}.json"
    citySettingsPath = "/var/www/django-project/Parkify/data/citySettings/ParkSettings.json"

    #************************* Instanzierung *************************#
    user = UserdataSheet(userPath)
    city = SettingsdataSheet(citySettingsPath)

    #************************* Verarbeitung *************************#
    if parkdauer:
        user.startParking(autoAuswahl, parkplatzWahl, parkdauer, parkpreisInEuro, city)

        
    vars = {
        "Username": user.username,
        "accname": accname,
        "pwd": pwd,
        "fahrzeuge": user.fahrzeuge,
        "ParkplatzOne": city.parkplaetze[0]["belegt"],
        "ParkplatzTwo": city.parkplaetze[1]["belegt"],
        "AktiveParkvorgaenge": user.numberOfActiveParkings(),
        "Preis": city.parkPreisProMinute

    }


    return render(request, "/var/www/django-project/Parkify/templates/Parkify/Home.html", vars)

def userHistory(request):
    accname = request.GET.get("accname", "")
    pwd = request.GET.get("pwd", "")
    startTime = request.GET.get("Start", "")
    numberplate = request.GET.get("numberplate", "")
    parkplatz = request.GET.get("parkplatz", "")

    class SettingsdataSheet():
        def __init__(self, settingsPath):
            self.path = settingsPath
            self.stadt = ""
            self.parkraum = ""
            self.abschleppUnternehmen = ""
            self.parkPreisProMinute = ""
            self.hoechstParkDauerInH = 0
            self.toleranzInProzent = 0
            self.parkplaetze = []

            self.load()

        def load(self):
            with open(self.path, "r") as file:
                settingsData = json.load(file)

            self.stadt = settingsData["Stadt"]
            self.parkraum = settingsData["Parkraum"]
            self.abschleppUnternehmen = settingsData["KontaktAbschleppunternehmen"]
            self.parkPreisProMinute = settingsData["ParkPreisProMinute"]
            self.hoechstParkDauerInH = settingsData["HoechstparkdauerInH"]
            self.toleranzInProzent = settingsData["ToleranzInProzent"]
            self.parkplaetze = []
            for item in settingsData["Parkplaetze"]:
                self.parkplaetze.append(item)
        
        def save(self):
            saveData = {
                "Stadt": self.stadt,
                "Parkraum": self.parkraum,
                "KontaktAbschleppunternehmen": self.abschleppUnternehmen,
                "ParkPreisProMinute": self.parkPreisProMinute,
                "HoechstparkdauerInH": self.hoechstParkDauerInH,
                "ToleranzInProzent": self.toleranzInProzent,
                "Parkplaetze": self.parkplaetze
            }

            with open(self.path, "w") as file:
                file.write(json.dumps(saveData, indent = 3))


    class UserdataSheet():
        def __init__(self, userPath):
            self.path = userPath
            self.username = ""
            self.pwd = ""
            self.email = ""
            self.status = ""
            self.lastLogin = ""
            self.anzahlMahnungen = ""
            self.anzahlAbschleppungen = ""
            self.parkKarteVorhanden = ""
            self.gesperrt = ""
            self.fahrzeuge = []

            self.load()

        def load(self):
            with open(self.path, "r") as file:
                userData = json.load(file)
            
            self.username = userData["username"]
            self.pwd = userData["pwd"]
            self.email = userData["email"]
            self.status = userData["status"]
            self.lastLogin = userData["letzterLogIn"]
            self.anzahlMahnungen = userData["anzahlMahnungen"]
            self.anzahlAbschleppungen = userData["anzahlAbschleppungen"]
            self.parkKarteVorhanden = userData["ParkkarteVorhanden"]
            self.gesperrt = userData["gesperrt"]
            self.fahrzeuge = []
            for item in userData["fahrzeuge"]:
                self.fahrzeuge.append(item)

        def emailsenden(self, betreff, inhalt):
            absender = "web.app.parkify@gmail.com"
            passwort = "nctktlekanowgzay"
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(absender, passwort)


            msg = EmailMessage()
            msg["From"] = absender
            msg["To"] = self.email
            msg["Subject"] = betreff
            msg.set_content(inhalt)

            server.send_message(msg)
            server.quit()


        def stopParkingAndCalculatePrice(self, Kennzeichen, Parkplatz, Startzeit, cityElement):
            for item in self.fahrzeuge:
                if Kennzeichen in item["Kennzeichen"]:
                    for entry in item["Parkhistorie"]:
                        if entry["Start"] == Startzeit:
                            entry["Ende"] = str(datetime.now(tz).time().strftime("%H:%M:%S"))
                            timeStart = datetime.strptime(entry["Start"], "%H:%M:%S")
                            timeEnd = datetime.strptime(entry["Ende"], "%H:%M:%S")
                            parkingTime = timeEnd - timeStart
                            Preis = round(parkingTime.total_seconds() / 60 * cityElement.parkPreisProMinute, 2)

                            entry["GesamtpreisInEuro"] = Preis

                            self.save()

                            mailtext = f"""\
                                Hallo {self.username},

                                Ihre Parkzeit ist beendet.

                                Fahrzeug: {Kennzeichen}
                                Parkplatz: {Parkplatz}
                                Startzeit: {Startzeit}
                                Endzeit: {entry['Ende']}
                                Kosten: {entry['GesamtpreisInEuro']} €

                                Vielen Dank für die Nutzung von Parkify!

                                Ihr Parkify-Team
                            """
                            self.emailsenden("Ihre Parkrechnung", mailtext)



                    for place in cityElement.parkplaetze:
                        if str(Parkplatz) in place["name"]:
                            place["belegt"] = False
                            for eintrag in place["Parkverlauf"]:
                                if eintrag["Start"] == Startzeit:
                                    eintrag["Ende"] == str(datetime.now(tz).time().strftime("%H:%M:%S"))

                            cityElement.save()


        def save(self):
            saveData = {
                "username": self.username,
                "pwd": self.pwd,
                "email": self.email,
                "status": self.status,
                "letzterLogIn": datetime.now(tz).strftime("%d.%m.%Y, %H:%M"),
                "anzahlMahnungen": self.anzahlMahnungen,
                "anzahlAbschleppungen": self.anzahlAbschleppungen,
                "ParkkarteVorhanden": self.parkKarteVorhanden,
                "gesperrt": self.gesperrt,
                "fahrzeuge": self.fahrzeuge
            }

            with open(self.path, "w") as file:
                file.write(json.dumps(saveData, indent = 3))


 

    #************************* Dateipfade *************************#
    citySettingsPath = "/var/www/django-project/Parkify/data/citySettings/ParkSettings.json"
    userPath = f"/var/www/django-project/Parkify/data/users/{accname}.json"

    #************************* Instanzierung *************************#
    user = UserdataSheet(userPath)
    city = SettingsdataSheet(citySettingsPath)

    #************************* Verarbeitung *************************#
    if startTime:
        user.stopParkingAndCalculatePrice(numberplate, parkplatz, startTime, city)



    vars = {
        "userData": user,
        "carData": user.fahrzeuge,
        "accname": accname,
        "pwd": pwd
    }


    return render(request, "/var/www/django-project/Parkify/templates/Parkify/History.html", vars)

def userPageSettings(request):

    accname = request.GET.get("accname", "")
    pwd = request.GET.get("pwd", "")
    neuesPwd = request.GET.get("neuesPwd", "")
    neuerUsername = request.GET.get("neuerUsername", "")
    neueEmail = request.GET.get("neueEmail", "")
    parkKarte = request.GET.get("parkKarte", "")
    neuesKennzeichen = request.GET.get("neuesKennzeichen", "")
    neuesCountry = request.GET.get("neuesCountry", "")
    newAvatarForAddingCar = request.GET.get("newAvatarForAddingCar", "")
    neuerAvatar = request.GET.get("neuerAvatar", "")
    autoNeuerAvatar = request.GET.get("carSelection", "")
    changedPlate = request.GET.get("changedPlate", "")
    carSelectionForPlateSwap = request.GET.get("carSelectionForPlateSwap", "")
    deleteCar = request.GET.get("carSelectionForDeleting", "")


    class Avatar():
        def __init__(self, path):
            self.path = path
            self.cars = []

            self.load()
        
        def load(self):
            with open(self.path, "r") as file:
                carData = json.load(file)

            for car in carData:
                self.cars.append(car)
                    
        def returnChosenAvatarLinks(self, avatarName):
            for car in self.cars:
                if avatarName in car["name"]:
                    return car
            
 

    class SettingsdataSheet():
        def __init__(self, settingsPath):
            self.path = settingsPath
            self.stadt = ""
            self.parkraum = ""
            self.abschleppUnternehmen = ""
            self.parkPreisProMinute = ""
            self.hoechstParkDauerInH = 0
            self.toleranzInProzent = 0
            self.parkplaetze = []

            self.load()

        def load(self):
            with open(self.path, "r") as file:
                settingsData = json.load(file)

            self.stadt = settingsData["Stadt"]
            self.parkraum = settingsData["Parkraum"]
            self.abschleppUnternehmen = settingsData["KontaktAbschleppunternehmen"]
            self.parkPreisProMinute = settingsData["ParkPreisProMinute"]
            self.hoechstParkDauerInH = settingsData["HoechstparkdauerInH"]
            self.toleranzInProzent = settingsData["ToleranzInProzent"]
            self.parkplaetze = []
            for item in settingsData["Parkplaetze"]:
                self.parkplaetze.append(item)
        
        def save(self):
            saveData = {
                "Stadt": self.stadt,
                "Parkraum": self.parkraum,
                "KontaktAbschleppunternehmen": self.abschleppUnternehmen,
                "ParkPreisProMinute": self.parkPreisProMinute,
                "HoechstparkdauerInH": self.hoechstParkDauerInH,
                "ToleranzInProzent": self.toleranzInProzent,
                "Parkplaetze": self.parkplaetze
            }

            with open(self.path, "w") as file:
                file.write(json.dumps(saveData, indent = 3))


    class UserdataSheet():
        def __init__(self, userPath):
            self.path = userPath
            self.username = ""
            self.pwd = ""
            self.email = ""
            self.status = ""
            self.lastLogin = ""
            self.anzahlMahnungen = ""
            self.anzahlAbschleppungen = ""
            self.parkKarteVorhanden = ""
            self.gesperrt = ""
            self.fahrzeuge = []

            self.load()
            #self.save()

        def load(self):
            with open(self.path, "r") as file:
                userData = json.load(file)
            
            self.username = userData["username"]
            self.pwd = userData["pwd"]
            self.email = userData["email"]
            self.status = userData["status"]
            self.lastLogin = userData["letzterLogIn"]
            self.anzahlMahnungen = userData["anzahlMahnungen"]
            self.anzahlAbschleppungen = userData["anzahlAbschleppungen"]
            self.parkKarteVorhanden = userData["ParkkarteVorhanden"]
            self.gesperrt = userData["gesperrt"]
            self.fahrzeuge = []
            for item in userData["fahrzeuge"]:
                self.fahrzeuge.append(item)
            
        def changeValue(self, valueToChange, newValue):
            setattr(self, valueToChange, newValue)

            self.save()

        def changeSkin(self, newSkin, platenumber, avatarElement):
            for item in self.fahrzeuge:
                if platenumber in item["Kennzeichen"]:
                    for option in avatarElement.cars:
                        if newSkin in option["name"]:
                            item["Avatar"] = option

                            self.save()

        def changeCurrentPlate(self, newPlate, oldPlate):
            for item in self.fahrzeuge:
                if oldPlate in item["Kennzeichen"]:
                    item["Kennzeichen"] = newPlate.upper()

                    self.save()
        
        def addNewCar(self, numberPlate, country, chosenSkin, avatarElement):
            avatarLinks = ""

            for item in avatarElement.cars:
                if chosenSkin in item["name"]:
                    avatarLinks = item

            newCarTempl = {
                "Landerkennung": country,
                "Kennzeichen": numberPlate.upper(),
                "Avatar": avatarLinks,
                "Parkhistorie": []
            }

            self.fahrzeuge.append(newCarTempl)

            self.save()

        def deleteCurrentCar(self, carToDelete):
            for item in self.fahrzeuge:
                if carToDelete in item["Kennzeichen"]:
                    self.fahrzeuge.remove(item)

                    self.save()
 
        def save(self):
            saveData = {
                "username": self.username,
                "pwd": self.pwd,
                "email": self.email,
                "status": self.status,
                "letzterLogIn": datetime.now().strftime("%d.%m.%Y, %H:%M"),
                "anzahlMahnungen": self.anzahlMahnungen,
                "anzahlAbschleppungen": self.anzahlAbschleppungen,
                "ParkkarteVorhanden": self.parkKarteVorhanden,
                "gesperrt": self.gesperrt,
                "fahrzeuge": self.fahrzeuge
            }

            with open(self.path, "w") as file:
                file.write(json.dumps(saveData, indent = 3))

    #************************* Dateipfade *************************#
    carAvatarPath = "/var/www/django-project/Parkify/data/Bilder/Cars/cars.json"
    userPath = f"/var/www/django-project/Parkify/data/users/{accname}.json"
    citySettingsPath = "/var/www/django-project/Parkify/data/citySettings/ParkSettings.json"

    #************************* Instanzierung *************************#
    user = UserdataSheet(userPath)
    city = SettingsdataSheet(citySettingsPath)
    avatars = Avatar(carAvatarPath)

    #************************* Verarbeitung *************************#

    if pwd == user.pwd:
        if neuesPwd:
            user.changeValue("pwd", neuesPwd)

        if neuerUsername:
            user.changeValue("username", neuerUsername)

        if neueEmail:
            user.changeValue("email", neueEmail)

        if parkKarte:
            if parkKarte == "0":
                user.changeValue("parkKarteVorhanden", False)
            elif parkKarte == "1":
                user.changeValue("parkKarteVorhanden", True)
        
        if neuerAvatar:
            user.changeSkin(neuerAvatar, autoNeuerAvatar, avatars)

        if changedPlate:
            user.changeCurrentPlate(changedPlate, carSelectionForPlateSwap)
        
        if neuesKennzeichen:
            user.addNewCar(neuesKennzeichen, neuesCountry, newAvatarForAddingCar, avatars)

        if deleteCar:
            user.deleteCurrentCar(deleteCar)

        
    vars = {
        "accname": accname,
        "pwd": pwd,
        "userData": user,
        "fahrzeuge": user.fahrzeuge,
        "cityData": city,
        "PreisProStunde": city.parkPreisProMinute * 60,
        "avatarsToChoose": avatars.cars
    }


    return render(request, "/var/www/django-project/Parkify/templates/Parkify/Settings.html", vars)

def adminPage(request):
    accname = request.GET.get("accname", "")
    pwd = request.GET.get("pwd", "")
    neuerPreis = request.GET.get("neuerPreis", "")
    neuerAbchlepper = request.GET.get("neuerAbschlepper", "")
    neueHoechstparkDauer = request.GET.get("neueHoechstparkDauer", "")
    neueToleranz = request.GET.get("neueToleranz", "")
    parkplatzManuelBefreien = request.GET.get("parkplatzManuelBefreien", "")
    deleteUser = request.GET.get("deleteUser", "")


    class Avatar():
        def __init__(self, path):
            self.path = path
            self.cars = []

            self.load()
        
        def load(self):
            with open(self.path, "r") as file:
                carData = json.load(file)

            for car in carData:
                self.cars.append(car)
                    
        def returnChosenAvatarLinks(self, avatarName):
            for car in self.cars:
                if avatarName in car["name"]:
                    return car
            
 

    class SettingsdataSheet():
        def __init__(self, settingsPath):
            self.path = settingsPath
            self.stadt = ""
            self.parkraum = ""
            self.abschleppUnternehmen = ""
            self.parkPreisProMinute = ""
            self.hoechstParkDauerInH = 0
            self.toleranzInProzent = 0
            self.parkplaetze = []

            self.load()

        def load(self):
            with open(self.path, "r") as file:
                settingsData = json.load(file)

            self.stadt = settingsData["Stadt"]
            self.parkraum = settingsData["Parkraum"]
            self.abschleppUnternehmen = settingsData["KontaktAbschleppunternehmen"]
            self.parkPreisProMinute = settingsData["ParkPreisProMinute"]
            self.hoechstParkDauerInH = settingsData["HoechstparkdauerInH"]
            self.toleranzInProzent = settingsData["ToleranzInProzent"]
            self.parkplaetze = []
            for item in settingsData["Parkplaetze"]:
                self.parkplaetze.append(item)

        def changeValue(self, valueToChange, newValue):
            setattr(self, valueToChange, newValue)

            self.save()

        def deleteSpecificiUser(self, userToDelete):
            deletePath = f"/var/www/django-project/Parkify/data/users/{userToDelete}.json"
            os.remove(deletePath)
        
        def save(self):
            saveData = {
                "Stadt": self.stadt,
                "Parkraum": self.parkraum,
                "KontaktAbschleppunternehmen": self.abschleppUnternehmen,
                "ParkPreisProMinute": self.parkPreisProMinute,
                "HoechstparkdauerInH": self.hoechstParkDauerInH,
                "ToleranzInProzent": self.toleranzInProzent,
                "Parkplaetze": self.parkplaetze
            }

            with open(self.path, "w") as file:
                file.write(json.dumps(saveData, indent = 3))


    class UserdataSheet():
        def __init__(self, userPath):
            self.path = userPath
            self.username = ""
            self.pwd = ""
            self.email = ""
            self.status = ""
            self.lastLogin = ""
            self.anzahlMahnungen = ""
            self.anzahlAbschleppungen = ""
            self.parkKarteVorhanden = ""
            self.gesperrt = ""
            self.fahrzeuge = []

            self.load()

        def load(self):
            with open(self.path, "r") as file:
                userData = json.load(file)
            
            self.username = userData["username"]
            self.pwd = userData["pwd"]
            self.email = userData["email"]
            self.status = userData["status"]
            self.lastLogin = userData["letzterLogIn"]
            self.anzahlMahnungen = userData["anzahlMahnungen"]
            self.anzahlAbschleppungen = userData["anzahlAbschleppungen"]
            self.parkKarteVorhanden = userData["ParkkarteVorhanden"]
            self.gesperrt = userData["gesperrt"]
            self.fahrzeuge = []
            for item in userData["fahrzeuge"]:
                self.fahrzeuge.append(item)
                        
        def changeValue(self, valueToChange, newValue):
            setattr(self, valueToChange, newValue)

            self.save()

        def changeSkin(self, newSkin, platenumber, avatarElement):
            for item in self.fahrzeuge:
                if platenumber in item["Kennzeichen"]:
                    for option in avatarElement.cars:
                        if newSkin in option["name"]:
                            item["Avatar"] = option

                            self.save()
 
        def save(self):
            saveData = {
                "username": self.username,
                "pwd": self.pwd,
                "email": self.email,
                "status": self.status,
                "letzterLogIn": datetime.now().strftime("%d.%m.%Y, %H:%M"),
                "anzahlMahnungen": self.anzahlMahnungen,
                "anzahlAbschleppungen": self.anzahlAbschleppungen,
                "ParkkarteVorhanden": self.parkKarteVorhanden,
                "gesperrt": self.gesperrt,
                "fahrzeuge": self.fahrzeuge
            }

            with open(self.path, "w") as file:
                file.write(json.dumps(saveData, indent = 3))

    #************************* Dateipfade *************************#
    carAvatarPath = "/var/www/django-project/Parkify/data/Bilder/Cars/cars.json"
    userPath = f"/var/www/django-project/Parkify/data/users/{accname}.json"
    citySettingsPath = "/var/www/django-project/Parkify/data/citySettings/ParkSettings.json"
    allUserPath = "/var/www/django-project/Parkify/data/users/"

    #************************* Instanzierung *************************#
    user = UserdataSheet(userPath)
    city = SettingsdataSheet(citySettingsPath)
    avatars = Avatar(carAvatarPath)

    allUser = []
    allUserData = []

    files = os.listdir(allUserPath)
    for file in files:
        if file.endswith('.json'):
            allUser.append(os.path.join(allUserPath, file))

    for user in allUser:
        data = UserdataSheet(user)
        allUserData.append(data)
        


    #************************* Verarbeitung *************************#
        
    vars = {
        "accname": accname,
        "pwd": pwd,
        "userData": user,
        "fahrzeuge": user.fahrzeuge,
        "cityData": city,
        "PreisProStunde": city.parkPreisProMinute * 60,
        "avatarsToChoose": avatars.cars,
        "alleUser": allUserData
    }


    return render(request, "/var/www/django-project/Parkify/templates/Parkify/Admin.html", vars)

def commandTranslator(request):
    #mailPath = "/var/www/django-project/Parkify/data/Mailbox/Mailbox_ParkingLot.json"

    changeParkingLotStatusTo = request.GET.get("changeParkingLotStatus", "")
    parkingLotNr = request.GET.get("Parkplatznummer", "")
    bookingStatus = request.GET.get("bookingStatus")
    parkByCard = request.GET.get("parkByCard", "")
    plate = request.GET.get("plate", "")
    sendMail = request.GET.get("sendMail", "")


    class SettingsdataSheet():
        def __init__(self, settingsPath):
            self.path = settingsPath
            self.userpath = "/var/www/django-project/Parkify/data/users/"
            self.stadt = ""
            self.parkraum = ""
            self.abschleppUnternehmen = ""
            self.parkPreisProMinute = ""
            self.hoechstParkDauerInH = 0
            self.toleranzInProzent = 0
            self.parkplaetze = []

            self.load()

        def load(self):
            with open(self.path, "r") as file:
                settingsData = json.load(file)

            self.stadt = settingsData["Stadt"]
            self.parkraum = settingsData["Parkraum"]
            self.abschleppUnternehmen = settingsData["KontaktAbschleppunternehmen"]
            self.parkPreisProMinute = settingsData["ParkPreisProMinute"]
            self.hoechstParkDauerInH = settingsData["HoechstparkdauerInH"]
            self.toleranzInProzent = settingsData["ToleranzInProzent"]
            self.parkplaetze = []
            for item in settingsData["Parkplaetze"]:
                self.parkplaetze.append(item)

        def changeParkingLotStatus(self, parkNr, status):
            for item in self.parkplaetze:
                if parkNr in item["name"]:
                    if status == "frei":
                        item["belegt"] = False
                        self.save()
                        for file in os.listdir(self.userpath):
                            if file.endswith(".json"):
                                filepath = os.path.join(self.userpath, file)
                                with open(filepath, "r", encoding="utf-8") as userFile:
                                    userData = json.load(userFile)
                                for entry in userData["fahrzeuge"]:
                                    for eintrag in entry["Parkhistorie"]:
                                        if eintrag["Ende"] == 0 and eintrag["Parkplatz"] in parkNr:
                                            eintrag["Ende"] = str(datetime.now(tz).time().strftime("%H:%M:%S"))
                                            timeStart = datetime.strptime(eintrag["Start"], "%H:%M:%S")
                                            timeEnd = datetime.strptime(eintrag["Ende"], "%H:%M:%S")
                                            parkingTime = timeEnd - timeStart
                                            Preis = round(parkingTime.total_seconds() / 60 * self.parkPreisProMinute, 2)
                                            eintrag["GesamtpreisInEuro"] = Preis

                                            with open(filepath, "w", encoding="utf-8") as saveFile:
                                                json.dump(userData, saveFile, indent=4)
                                            
                                            for endZeit in item["Parkverlauf"]:
                                                if endZeit["Ende"] == 0:
                                                    endZeit["Ende"] = str(datetime.now(tz).time().strftime("%H:%M:%S"))
                                                    self.save()

                    elif status == "belegt" and item["belegt"] == False:
                        item["belegt"] = None
                        self.save()
                    elif status == "belegt" and item["belegt"] == True:
                        pass

        def __createNewAccountByBurgercard(self, email):
            username = email.split("@")[0]
            accountname = email.split("@")[0]
            pwd = email[:3]
            country = "D"
            numberPlate = email[:3]

            requests.get(f"http://[2001:7c0:2320:2:f816:3eff:fe82:34b2]:8000/Parkify/Loading?username={username}&accname={accountname}&email={email}&pwd={pwd}&country={country}&numberplate={numberPlate}")

            for item in self.parkplaetze:
                if item["belegt"] == None:

                    neuerEintragUser = {
                        "Datum": str(datetime.now(tz).strftime("%d.%m.%Y")),
                        "Stadt": self.stadt,
                        "Parkraum": self.parkraum,
                        "Parkplatz": item["name"],
                        "GebuchteDauer": 0,
                        "Start": str(datetime.now(tz).time().strftime("%H:%M:%S")),
                        "Ende": 0,
                        "GesamtpreisInEuro": 0
                    }

                    neuerEintragParkplatz = {
                        "Datum": str(datetime.now(tz).strftime("%d.%m.%Y")),
                        "Kennzeichen": numberPlate,
                        "Start": str(datetime.now(tz).time().strftime("%H:%M:%S")),
                        "Ende": 0
                    }

                    item["Parkverlauf"].append(neuerEintragParkplatz)
                    item["belegt"] = True
                    filename = accountname + ".json"
                    filepath = os.path.join(self.userpath, filename)

                    with open(filepath, "r", encoding="utf-8") as userFile:
                        userData = json.load(userFile)

                    userData["fahrzeuge"][0]["Parkhistorie"].append(neuerEintragUser)
                    with open(filepath, "w", encoding="utf-8") as saveFile:
                        json.dump(userData, saveFile, indent=4)

                    self.save()




        def startParkingByCard(self, plate):
            if "@" in plate:
                userNumber = len(os.listdir(self.userpath))
                counter = 0
                userFound = False

                for counter, file in enumerate(os.listdir(self.userpath), start=1):
                    counter += 1
                    filepath = os.path.join(self.userpath, file)
                    with open(filepath, "r", encoding="utf-8") as userFile:
                        userData = json.load(userFile)

                    if plate == userData["email"]:
                        userFound = True
                        for item in self.parkplaetze:
                            if item["belegt"] == None:

                                neuerEintragUser = {
                                    "Datum": str(datetime.now(tz).strftime("%d.%m.%Y")),
                                    "Stadt": self.stadt,
                                    "Parkraum": self.parkraum,
                                    "Parkplatz": item["name"],
                                    "GebuchteDauer": 0,
                                    "Start": str(datetime.now(tz).time().strftime("%H:%M:%S")),
                                    "Ende": 0,
                                    "GesamtpreisInEuro": 0
                                }

                                neuerEintragParkplatz = {
                                    "Datum": str(datetime.now(tz).strftime("%d.%m.%Y")),
                                    "Kennzeichen": plate,
                                    "Start": str(datetime.now(tz).time().strftime("%H:%M:%S")),
                                    "Ende": 0
                                }

                                item["Parkverlauf"].append(neuerEintragParkplatz)
                                item["belegt"] = True
                                
                                userData["fahrzeuge"][0]["Parkhistorie"].append(neuerEintragUser)
                                with open(filepath, "w", encoding="utf-8") as saveFile:
                                    json.dump(userData, saveFile, indent=4)

                                self.save()
                                return
                    break

                if not userFound:
                    self.__createNewAccountByBurgercard(plate)



            else:
                try:
                    for file in os.listdir(self.userpath):
                        filepath = os.path.join(self.userpath, file)
                        with open(filepath, "r", encoding="utf-8") as userFile:
                            userData = json.load(userFile)

                        for entry in userData["fahrzeuge"]:
                            if plate.upper() in entry["Kennzeichen"]:
                                for item in self.parkplaetze:
                                    if item["belegt"] == None:

                                        neuerEintragUser = {
                                            "Datum": str(datetime.now(tz).strftime("%d.%m.%Y")),
                                            "Stadt": self.stadt,
                                            "Parkraum": self.parkraum,
                                            "Parkplatz": item["name"],
                                            "GebuchteDauer": 0,
                                            "Start": str(datetime.now(tz).time().strftime("%H:%M:%S")),
                                            "Ende": 0,
                                            "GesamtpreisInEuro": 0
                                        }

                                        neuerEintragParkplatz = {
                                            "Datum": str(datetime.now(tz).strftime("%d.%m.%Y")),
                                            "Kennzeichen": plate,
                                            "Start": str(datetime.now(tz).time().strftime("%H:%M:%S")),
                                            "Ende": 0
                                        }

                                        item["Parkverlauf"].append(neuerEintragParkplatz)
                                        item["belegt"] = True

                                        entry["Parkhistorie"].append(neuerEintragUser)
                                        with open(filepath, "w", encoding="utf-8") as saveFile:
                                            json.dump(userData, saveFile, indent=4)

                                        self.save()
                                        
                                
                                    else:
                                        pass
                            else:
                                pass
                        
                except:
                    pass
    

        def emailsenden(self, email, betreff, Kennzeichen, Start, Ende, Preis, Parkplatz, Username):
            absender = "web.app.parkify@gmail.com"
            passwort = "nctktlekanowgzay"
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(absender, passwort)

            mailtext = f"""\
                Hallo {Username},

                Ihre Parkzeit ist beendet.

                Fahrzeug: {Kennzeichen}
                Parkplatz: {Parkplatz}
                Startzeit: {Start}
                Endzeit: {Ende}
                Kosten: {Preis} €

                Vielen Dank für die Nutzung von Parkify!

                Ihr Parkify-Team
            """

            msg = EmailMessage()
            msg["From"] = absender
            msg["To"] = email
            msg["Subject"] = betreff
            msg.set_content(mailtext)

            server.send_message(msg)
            server.quit()


                
                
        
        def returnBookingStatus(self, parkNr):
            for item in self.parkplaetze:
                if parkNr in item["name"]:
                    status = str(item["belegt"])
                    return status
                    
        def save(self):
            saveData = {
                "Stadt": self.stadt,
                "Parkraum": self.parkraum,
                "KontaktAbschleppunternehmen": self.abschleppUnternehmen,
                "ParkPreisProMinute": self.parkPreisProMinute,
                "HoechstparkdauerInH": self.hoechstParkDauerInH,
                "ToleranzInProzent": self.toleranzInProzent,
                "Parkplaetze": self.parkplaetze
            }

            with open(self.path, "w") as file:
                file.write(json.dumps(saveData, indent = 3))


    #************************* Dateipfade *************************#
    citySettingsPath = "/var/www/django-project/Parkify/data/citySettings/ParkSettings.json"

    #************************* Instanzierung *************************#
    city = SettingsdataSheet(citySettingsPath)

    #************************* Verarbeitung *************************#
    if changeParkingLotStatusTo:
        city.changeParkingLotStatus(parkingLotNr, changeParkingLotStatusTo)

    if bookingStatus:
        return HttpResponse(city.returnBookingStatus(bookingStatus))
    
    if parkByCard and plate:
        city.startParkingByCard(plate)
    

