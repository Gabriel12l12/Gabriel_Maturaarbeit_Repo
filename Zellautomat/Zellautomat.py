#  -*- coding: cp1252 -*-
import taichi as ti
import taichi.math as tm
import numpy as np
import json
import os
import matplotlib
import tkinter
import csv

#Der Seed 39487598

start = True
while start:
    seedText = input("Gib einen Seed ein: ")
    if len(seedText) <= 10 and seedText.isdigit():
        start = False
        seed = int(seedText)

    elif seedText.isdigit():
        print("Seed zu lang, unter 10 Zeichen")
    else:
        print("Nur Zahlen")

headName =  "\\HeadResults\\"
headlessName = "\\HeadlessResults\\"
HeadlessOrdnerPath = os.path.dirname(os.path.abspath(__file__))

resolution = (800, 800)

maxWidth = 3000
maxHeight = 3000
width = 5
height = 5

referenzAlter = 60


renderHeight = 1080
renderWidth = 1080

ti.init(arch=ti.gpu, random_seed=seed)

#Struct fur die Zelle

Cell = ti.types.struct(

    #Von Claude vorgeschlagen ti.u8 --> ti.u32
    status=ti.i32,

    age=ti.i32,

    householdID=ti.i32,
    maxHouseholdSize=ti.i32,

    #Von Claude vorgeschlagen ti.u8 --> ti.u32
    currentHouseholdSize=ti.i32,

    baseSocialFactor=ti.i32,
    socialFactor=ti.i32,

    incubationTimer=ti.i32,
    recoveryTimer=ti.i32)


def TaichiFieldsDefinieren(Cell, width, height, renderWidth, renderHeight):
    global erfolgreichInfiziert, gridAlt, grid, gridVorlage, gridColorField, statePallete, renderColorField, statusCounts

    erfolgreichInfiziert = ti.field(dtype=ti.i32, shape=())

    #Von Claude vorgeschlagen als counts ersatzt:
    statusCounts = ti.field(dtype=ti.i32, shape=4)


    gridAlt = Cell.field(shape=(width, height))
    grid = Cell.field(shape=(width, height))
    gridVorlage = Cell.field(shape=(width, height)) 

    gridColorField = ti.Vector.field(3, dtype=ti.f32, shape=(height, width))
    statePallete = ti.Vector.field(3, dtype=ti.f32, shape=4)
    renderColorField = ti.Vector.field(3, dtype=ti.f32, shape=(renderWidth, renderHeight))

    print("Felder Definiert")


@ti.kernel
def ResetGrid(width: ti.i32, height: ti.i32,grid: ti.template(), gridVorlage: ti.template(), gridAlt:ti.template()):
    for i, j in ti.ndrange(width, height):
        grid[i, j] = gridVorlage[i, j]
        gridAlt[i, j] = gridVorlage[i, j] #Mit Hilfe von Claude gefunden, selber gelöst


def ResetTaichiFields():
    erfolgreichInfiziert[None] = 0 

    ResetGrid(width, height,grid, gridVorlage, gridAlt)

    print("Felder reseten")



TaichiFieldsDefinieren(Cell, width, height, renderWidth, renderHeight)


#Simulation States
simulationRunning = False
mode = 0
setup = False

#Variabeln fuer Headless mode
headlessMode = False
anzahlHeadlessDurchlaufe = 100
durchlauf = 1

tag = 0

#Demografie Eingabe
childDemo = 0
adultDemo = 0
rentnerDemo = 0
plusDemo = 0
demoFehler = False

#Haushalt eingabe
einsHaushalt = 0
zweiHaushalt = 0
dreiHaushalt = 0
vierHaushalt = 0
fuenfHaushalt = 0
plusSechs = 0
haushaltFehler = False

#Konfigration der Zellen
demografie = np.array([], dtype=np.float32)
householdData = np.array([], dtype=np.float32)

startKranke = 0
socialInput = 0

window = ti.ui.Window("Zellautomat", resolution, vsync=False, fps_limit=200)
canvas = window.get_canvas()

#Berechnung
baseTransmissionrate = 0
transmissionrate = 0
householdFactor = 0

mortalityrate = 0
ageFactor = 0

incubationTime = 1
recoveryTime = 1

maxRadius = 1

wechsel = False


# Debug-Zaehler zur Diagnose der Ansteckungslogik
debugVersuche = ti.field(dtype=ti.i32, shape=())
debugErfolge = ti.field(dtype=ti.i32, shape=())

#Speichern/Laden
SpeicherDatei = "einstellungen.json"
statusMeldung = ""
statusMeldungTimer = 0
csvSpeicherName = "Ergebnisse"

seedDateiname = "SeedHistory.json"

simulationsverlauf = []
durchlaufSicherungsFrequenz = 100



#==============
#Speichern / Laden
#===============

def SammleParameter():
    """Sammelt alle im GUI einstellbaren Parameter in einem Dictionary."""
    return {
        "width": width,
        "height": height,

        "childDemo": childDemo,
        "adultDemo": adultDemo,
        "rentnerDemo": rentnerDemo,
        "ageFactor": ageFactor,
        "socialInput": socialInput,

        "einsHaushalt": einsHaushalt,
        "zweiHaushalt": zweiHaushalt,
        "dreiHaushalt": dreiHaushalt,
        "vierHaushalt": vierHaushalt,
        "fuenfHaushalt": fuenfHaushalt,
        "householdFactor": householdFactor,

        "startKranke": startKranke,
        "baseTransmissionrate": baseTransmissionrate,
        "mortalityrate": mortalityrate,
        "maxRadius": maxRadius,
        "incubationTime": incubationTime,
        "recoveryTime": recoveryTime,
        "referenzAlter": referenzAlter,
    }

def SammleSeed():
    return {"seed" : seed}

def SpeichereSeed(seedDateiname):
    global statusMeldung, statusMeldungTimer
    try:
        daten = SammleSeed()
        with open(seedDateiname, "w", encoding="utf-8") as f:
            json.dump(daten, f, indent=4, ensure_ascii=False)
        statusMeldung = "Gespeichert: " + seedDateiname
    except Exception as e:
        statusMeldung = "Fehler beim Speichern: " + str(e)
    statusMeldungTimer = 120


def SpeichereParameter(dateiname):
    global statusMeldung, statusMeldungTimer
    try:
        daten = SammleParameter()
        with open(dateiname, "w", encoding="utf-8") as f:
            json.dump(daten, f, indent=4, ensure_ascii=False)
        statusMeldung = "Gespeichert: " + dateiname
    except Exception as e:
        statusMeldung = "Fehler beim Speichern: " + str(e)
    statusMeldungTimer = 120


def LadeParameter(dateiname):
    global width, height
    global childDemo, adultDemo, rentnerDemo, plusDemo, ageFactor, socialInput
    global einsHaushalt, zweiHaushalt, dreiHaushalt, vierHaushalt, fuenfHaushalt, plusSechs, householdFactor
    global startKranke, baseTransmissionrate, mortalityrate, maxRadius, incubationTime, recoveryTime
    global demoFehler, haushaltFehler, statusMeldung, statusMeldungTimer, referenzAlter

    try:
        if not os.path.exists(dateiname):
            statusMeldung = "Datei nicht gefunden: " + dateiname
            statusMeldungTimer = 120
            return

        with open(dateiname, "r", encoding="utf-8") as f:
            daten = json.load(f)

        width = int(daten.get("width", width))
        height = int(daten.get("height", height))


        childDemo = int(daten.get("childDemo", childDemo))
        adultDemo = int(daten.get("adultDemo", adultDemo))
        rentnerDemo = int(daten.get("rentnerDemo", rentnerDemo))
        ageFactor = float(daten.get("ageFactor", ageFactor))
        socialInput = float(daten.get("socialInput", socialInput))
        einsHaushalt = int(daten.get("einsHaushalt", einsHaushalt))
        zweiHaushalt = int(daten.get("zweiHaushalt", zweiHaushalt))
        dreiHaushalt = int(daten.get("dreiHaushalt", dreiHaushalt))
        vierHaushalt = int(daten.get("vierHaushalt", vierHaushalt))
        fuenfHaushalt = int(daten.get("fuenfHaushalt", fuenfHaushalt))
        householdFactor = float(daten.get("householdFactor", householdFactor))
        referenzAlter = int(daten.get("referenzAlter", referenzAlter))



        startKranke = int(daten.get("startKranke", startKranke))
        baseTransmissionrate = float(daten.get("baseTransmissionrate", baseTransmissionrate))
        mortalityrate = float(daten.get("mortalityrate", mortalityrate))
        maxRadius = int(daten.get("maxRadius", maxRadius))

        incubationTime = int(daten.get("incubationTime", incubationTime))
        recoveryTime = int(daten.get("recoveryTime", recoveryTime))

        plusDemo = 100 - (childDemo + adultDemo + rentnerDemo)
        demoFehler = plusDemo < 0

        plusSechs = 100 - (einsHaushalt + zweiHaushalt + dreiHaushalt + vierHaushalt + fuenfHaushalt)
        haushaltFehler = plusSechs < 0

        statusMeldung = "Geladen: " + dateiname
    except Exception as e:
        statusMeldung = "Fehler beim Laden: " + str(e)
    statusMeldungTimer = 120

#========
#Ergebnisse Speichern:
#=======

def writeCSV(simulationsverlauf, csvSpeicherName, seed):
    with open(csvSpeicherName + ".csv", "w", newline="", encoding= "utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Durchlauf", "Tag", "Gesund", "Krank","Immun", "Tot"])
        writer.writerows(simulationsverlauf)

        print("Seed: ", seed)


#==============
#Kernells
#===============


@ti.kernel
def InitializePallets(statePallete: ti.template()):
    statePallete[0] = ti.Vector([1.0, 1.0, 1.0], ti.f32)  # Gesund
    statePallete[1] = ti.Vector([1.0, 0, 0], ti.f32)  # Krank
    statePallete[2] = ti.Vector([0, 0, 1.0], ti.f32)  # Immun
    statePallete[3] = ti.Vector([0, 0, 0], ti.f32)  # Tot


@ti.kernel
def KrankheitsAusbruch(width: ti.i32, height: ti.i32, pWrite: ti.template(), erfolgreichInfiziert: ti.template(), startKranke: ti.i32):


    erfolgreichInfiziert[None] = 0
    versuche = 0
    maxVersuche = width * height * 20

    while erfolgreichInfiziert[None] < startKranke and versuche < maxVersuche:

        i = int(ti.random() * width)
        j = int(ti.random() * height)

        oldState = ti.atomic_max(pWrite[i, j].status, 1)

        if oldState == 0:
            ti.atomic_add(erfolgreichInfiziert[None], 1)

        versuche += 1


@ti.kernel
def InitializeAge(width: ti.i32, height: ti.i32, pWrite: ti.template(), demografie: ti.types.ndarray()):

    #Altersgenerierung
    for i, j in ti.ndrange(width, height):
        generatedAge = 0
        zufall = ti.random()

        if zufall <= demografie[0]:
            generatedAge = int(ti.random() * 20)

        elif zufall <= demografie[0] + demografie[1]:
            generatedAge = 20 + int(ti.random() * 44)

        elif zufall <= demografie[0] + demografie[1] + demografie[2]:
            generatedAge = 65 + int(ti.random() * 14)

        else:
            generatedAge = 80 + int(ti.random() * 10)

        pWrite[i, j].age = generatedAge


@ti.kernel
def InitializeSocial(width: ti.i32, height: ti.i32, pWrite: ti.template(), socialInput: ti.f32):

    for i, j in ti.ndrange(width, height):
        age = ti.cast(pWrite[i, j].age, ti.f32)

        altersFaktor = ti.max(0.1, 1.0 - (ti.pow(age - 20.0, 2) / 5000.0))

        zufallsKontakte = ti.cast(socialInput * ti.random() * altersFaktor, ti.i32)

        pWrite[i, j].socialFactor = zufallsKontakte + pWrite[i, j].currentHouseholdSize


@ti.kernel
def InitializeHouseholds(width: ti.i32, height: ti.i32, pWrite: ti.template(), haushalteDaten: ti.types.ndarray()):
    for i, j in ti.ndrange(width, height):

        pWrite[i, j].householdID = i * height + j + 1
        pWrite[i, j].currentHouseholdSize = 1

        zufall = ti.random()

        hZahl = 1
        if zufall <= haushalteDaten[0]:
            pass
        elif zufall <= haushalteDaten[0] + haushalteDaten[1]:
            hZahl = 2
        elif zufall <= haushalteDaten[0] + haushalteDaten[1] + haushalteDaten[2]:
            hZahl = 3
        elif zufall <= haushalteDaten[0] + haushalteDaten[1] + haushalteDaten[2] + haushalteDaten[3]:
            hZahl = 4
        elif zufall <= haushalteDaten[0] + haushalteDaten[1] + haushalteDaten[2] + haushalteDaten[3] + haushalteDaten[4]:
            hZahl = 5
        elif zufall <= haushalteDaten[0] + haushalteDaten[1] + haushalteDaten[2] + haushalteDaten[3] + haushalteDaten[4] + haushalteDaten[5]:
            hZahl = 6
        else:
            hZahl = 7 + int(ti.random() * 2)

        pWrite[i, j].maxHouseholdSize = hZahl


@ti.kernel
def CreateHouseholdsStep(width: ti.i32, height: ti.i32, pWrite: ti.template()):

    for i, j in ti.ndrange(width, height):

        if pWrite[i, j].currentHouseholdSize < pWrite[i, j].maxHouseholdSize:
            found = False

       
            for di in range(-1, 2):
                for dj in range(-1, 2):
                    if not found or (di != 0 or dj != 0):
                        ni = (i + di + width) % width
                        nj = (j + dj + height) % height

                        targetSingleID = ni * height + nj + 1

                        if pWrite[ni, nj].householdID == targetSingleID:

      
                            oldID = ti.atomic_min(pWrite[ni, nj].householdID, pWrite[i, j].householdID)

                            if oldID == targetSingleID:

                                if pWrite[ni, nj].householdID == pWrite[i, j].householdID:
                                    pWrite[i, j].currentHouseholdSize += 1
                                    found = True


@ti.kernel
def Calculation(width: ti.i32, height: ti.i32, pWrite: ti.template(), pRead: ti.template(), baseTransmissionrate: ti.f32, householdFactor: ti.f32, mortalityRate: ti.f32, ageFactor: ti.f32, incubationTime: ti.i32, recoveryTime: ti.i32, maxRadius: ti.i32, referenzAlter: ti.i32):

    for i, j in ti.ndrange(width, height):

        pWrite[i, j].age = pRead[i, j].age
        pWrite[i, j].householdID = pRead[i, j].householdID
        pWrite[i, j].maxHouseholdSize = pRead[i, j].maxHouseholdSize
        pWrite[i, j].currentHouseholdSize = pRead[i, j].currentHouseholdSize
        pWrite[i, j].socialFactor = pRead[i, j].socialFactor
        
        pWrite[i, j].incubationTimer = pRead[i, j].incubationTimer
        pWrite[i, j].recoveryTimer = pRead[i, j].recoveryTimer

        ti.atomic_max(pWrite[i, j].status, pRead[i, j].status)

        if pRead[i, j].status == 1:

            hatSymptome = pRead[i, j].recoveryTimer > 0

            kontakte = 0
            suchRadius = 0

            if hatSymptome:
                kontakte = pRead[i, j].currentHouseholdSize
                suchRadius = 2
            else:
                kontakte = pRead[i, j].socialFactor
                suchRadius = ti.cast(kontakte / 2, ti.i32)

            anzahlSuchen = 0
            cellAlter = pRead[i, j].age

            for di in range(-maxRadius, maxRadius + 1):
                for dj in range(-maxRadius, maxRadius + 1):

                    if anzahlSuchen < kontakte and ti.abs(di) <= suchRadius and ti.abs(dj) <= suchRadius:
                        if di != 0 or dj != 0:

                            ni = (i + di + width) % width
                            nj = (j + dj + height) % height

                            istGleicherHaushalt = pRead[ni, nj].householdID == pRead[i, j].householdID

                            if not(hatSymptome) or (hatSymptome and istGleicherHaushalt):
                                anzahlSuchen += 1

                                if pRead[ni, nj].status == 0:
                                    

                                    currentTransmissionrate = baseTransmissionrate

                                    if istGleicherHaushalt:
                                        currentTransmissionrate = baseTransmissionrate * ti.cast(householdFactor, ti.f32)

                                    if ti.random() <= currentTransmissionrate:
                                        
                                        ti.atomic_max(pWrite[ni, nj].status, 1)

  
            #Sterbeschance mit Bernoulli
            gesammteKrankheitsdauer = incubationTime + recoveryTime
            gesammtRisikoZelle = mortalityRate * ti.pow(ti.math.e,ti.cast(cellAlter - referenzAlter, ti.f32) * ageFactor)
            gesammtRisikoZelle = ti.max(0.0, ti.min(gesammtRisikoZelle, 1.0))
            taeglicheSterbechance = 1.0 - ti.pow(1.0 - gesammtRisikoZelle, 1.0 / ti.cast(gesammteKrankheitsdauer, ti.f32))

            if ti.random() <= taeglicheSterbechance:
                pWrite[i, j].status = 3
            else:

                if pRead[i, j].recoveryTimer >= ti.cast(recoveryTime,ti.i32):
                    pWrite[i, j].recoveryTimer = 0
                    pWrite[i, j].status = 2

                elif hatSymptome:
                    pWrite[i, j].recoveryTimer = pRead[i, j].recoveryTimer + 1

                elif pRead[i, j].incubationTimer >= incubationTime:
                    pWrite[i, j].incubationTimer = 0
                    pWrite[i, j].recoveryTimer = 1

                else:
                    pWrite[i, j].incubationTimer = pRead[i, j].incubationTimer + 1


@ti.kernel
def ColorCells(width: ti.i32, height: ti.i32, pWrite: ti.template(), gridColorField: ti.template(), statePallete: ti.template()):
    for i, j in ti.ndrange(width, height):
        cellAge = pWrite[i, j].age


        helligkeit = 1.0 - (ti.cast(cellAge, ti.f32) / 90.0) * 0.5

        gridColorField[j, width - i - 1] = statePallete[pWrite[i, j].status] * helligkeit

@ti.kernel 
def parallelGridCopy(width: ti.i32, height: ti.i32,pWrite: ti.template(), pRead: ti.template()):

    for i, j in ti.ndrange(width, height):
        pRead[i, j] = pWrite[i, j]



#Code Vorher
#@ti.kernel
#def ZaehleStatus(width: ti.i32, height: ti.i32, pWrite: ti.template()) -> tm.ivec4:
 #   counts = tm.ivec4(0, 0, 0, 0)
  #  for i, j in ti.ndrange(width, height):
   #     status_idx = ti.cast(pWrite[i, j].status, ti.i32)
    #    counts[status_idx] += 1
    #return counts

#Von Claude vorgeschlagen:
@ti.kernel
def ZaehleStatusNeu(width: ti.i32, height: ti.i32, pWrite: ti.template()):
    for k in range(4):
        statusCounts[k] = 0
    for i, j in ti.ndrange(width, height): #Die KI hat sich sogar an mein Muster mit ti.ndrange() zum loopen gehalten
        ti.atomic_add(statusCounts[ti.cast(pWrite[i, j].status, ti.i32)], 1)


@ti.kernel
def BildRunterskallieren(width: ti.i32, height: ti.i32, renderWidth: ti.i32, renderHeight: ti.i32, gridColorField: ti.template(), renderColorField: ti.template()):
    for i, j in ti.ndrange(renderWidth, renderHeight):

        simI = int((i / renderWidth) * width)
        simJ = int((j / renderHeight) * height)



        renderColorField[i, j] = gridColorField[simJ, simI]



while window.running:


    gui = window.get_gui()

    if statusMeldungTimer > 0:
        statusMeldungTimer -= 1

#==========================
#Simulation mit head
#===========================

    if simulationRunning == True:
        if headlessMode == False:
            with gui.sub_window("Simulation", x=0, y=0, width=0.3, height=0.25):

                    if gui.button("Stop"):
                        simulationRunning = False
        
            if setup:
                
                ResetTaichiFields()

                InitializePallets(statePallete)
        
                startKrankeSicher = min(startKranke, width * height)
        
                KrankheitsAusbruch(width, height, grid, erfolgreichInfiziert, startKrankeSicher)
    
                InitializeAge(width, height, grid, demografie)
   
                InitializeHouseholds(width, height, grid, householdData)
        
                InitializeSocial(width, height, grid, socialInput)
               

                for i in range(10):
                    CreateHouseholdsStep(width, height, grid)
                
                print("Setup fertig")
                setup = False
                wechsel = False

            #pointerSwap
            if wechsel:
                pWrite = grid
                pRead  = gridAlt
                wechsel = False
            else:
                pWrite = gridAlt
                pRead  = grid
                wechsel = True

            
            Calculation(width, height, pWrite, pRead, baseTransmissionrate * 0.01, householdFactor, mortalityrate * 0.01, ageFactor, incubationTime, recoveryTime, maxRadius, referenzAlter)
         
            ColorCells(width, height, pWrite, gridColorField, statePallete)
            BildRunterskallieren(width, height, renderWidth, renderHeight, gridColorField, renderColorField)

            tag += 1

            ZaehleStatusNeu(width, height, pWrite)

            simulationsverlauf.append([durchlauf, tag, statusCounts[0], statusCounts[1], statusCounts[2], statusCounts[3]])


            print(f"Tag {tag} | Gesund: {statusCounts[0]}  Krank: {statusCounts[1]}  Immun: {statusCounts[2]}  Tot: {statusCounts[3]}")

            #Ende vom Durchlauf
            if statusCounts[1] == 0:
                name = HeadlessOrdnerPath + headlessName + csvSpeicherName + str(durchlauf)
                writeCSV(simulationsverlauf, name, seed)
                simulationRunning == False
                mode = 1



        

#^==============================
#Headless Mde

        if headlessMode:
            if durchlauf <= anzahlHeadlessDurchlaufe:

                #Fields Setup fuer die Simulation
                if setup:
                
                    ResetTaichiFields()
        
                    startKrankeSicher = min(startKranke, width * height)
        
                    KrankheitsAusbruch(width, height, grid, erfolgreichInfiziert, startKrankeSicher)
    
                    InitializeAge(width, height, grid, demografie)
   
                    InitializeHouseholds(width, height, grid, householdData)
        
                    InitializeSocial(width, height, grid, socialInput)
               

                    for i in range(10):
                        CreateHouseholdsStep(width, height, grid)
                
                    print("Setup fertig")
                    setup = False
                    wechsel = False

                #pointerSwap
                if wechsel:
                    pWrite = grid
                    pRead  = gridAlt
                    wechsel = False
                else:
                    pWrite = gridAlt
                    pRead  = grid
                    wechsel = True

            
                Calculation(width, height, pWrite, pRead, baseTransmissionrate * 0.01, householdFactor, mortalityrate * 0.01, ageFactor, incubationTime, recoveryTime, maxRadius, referenzAlter)
         

                tag += 1

                ZaehleStatusNeu(width, height, pWrite)

                simulationsverlauf.append([durchlauf, tag, statusCounts[0], statusCounts[1], statusCounts[2], statusCounts[3]])


                print(f"Tag {tag} | Gesund: {statusCounts[0]}  Krank: {statusCounts[1]}  Immun: {statusCounts[2]}  Tot: {statusCounts[3]}")

                #Ende vom Durchlauf
                if statusCounts[1] == 0:
                    print("Durchlauf ", durchlauf, " Fertig!")

                    if durchlauf%durchlaufSicherungsFrequenz == 0:
                        name = HeadlessOrdnerPath + headlessName + csvSpeicherName + str(durchlauf)
                        print(name)
                        writeCSV(simulationsverlauf, name, seed)

                        simulationsverlauf = []
                        print("Daten Gesichert")


                    durchlauf += 1

                    #Reseten fuer naechsten Durchlauf
                    setup = True
                    tag = 0


            else:
                headlessMode = False
                simulationRunning =False
            





#==================================
#Hauptmenue  logik
#===================================

    else:
        # Allgemein ------------------
        with gui.sub_window("Hauptmenue", x=0, y=0, width=0.3, height=0.45):

            if gui.button("Headless mode start"):
                demografie = np.array([childDemo, adultDemo, rentnerDemo, plusDemo], dtype=np.float32) * 0.01
                householdData = np.array([einsHaushalt, zweiHaushalt, dreiHaushalt, vierHaushalt, fuenfHaushalt, plusSechs], dtype=np.float32) * 0.01

                SpeichereSeed(seedDateiname)

                headlessMode = True
                simulationRunning = True
                TaichiFieldsDefinieren(Cell, width, height, renderWidth, renderHeight)
                mode = 0
                setup = True
            gui.text("")

            #Start Button --------------------
            if demoFehler == False and haushaltFehler == False:
                if gui.button("Start"):

                    demografie = np.array([childDemo, adultDemo, rentnerDemo, plusDemo], dtype=np.float32) * 0.01
                    householdData = np.array([einsHaushalt, zweiHaushalt, dreiHaushalt, vierHaushalt, fuenfHaushalt, plusSechs], dtype=np.float32) * 0.01

                    SpeichereSeed(seedDateiname)

                    headlessMode = False
                    simulationRunning = True
                    TaichiFieldsDefinieren(Cell, width, height, renderWidth, renderHeight)
                    mode = 0
                    setup = True

            elif demoFehler == True:
                gui.text("Demografie bitte korrigieren")
            else:
                gui.text("Haushalt bitte korrigieren")

            gui.text("")

            if gui.button("Speichern"):
                SpeichereParameter(SpeicherDatei)
            if gui.button("Laden"):
                LadeParameter(SpeicherDatei)
                print(mortalityrate)

            if statusMeldungTimer > 0:
                gui.text(statusMeldung)
        
    if headlessMode == False:
        canvas.set_image(renderColorField)
        window.show()