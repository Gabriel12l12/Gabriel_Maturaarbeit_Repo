#  -*- coding: cp1252 -*-
import taichi as ti
import taichi.math as tm
import numpy as np
import json
import os
import matplotlib
import tkinter

seed = int(input("Gib einen Seed ein: "))


maxWidth = 3000
maxHeight = 3000
width = 5
height = 5


renderHeight = 1080
renderWidth = 1080

ti.init(arch=ti.gpu, random_seed=seed)

#Struct fur die Zelle

Cell = ti.types.struct(

    #Von Claude vorgeschlagen ti.u8 --> ti.u32
    status=ti.u32,

    age=ti.u8,

    householdID=ti.u32,
    maxHouseholdSize=ti.u8,

    #Von Claude vorgeschlagen ti.u8 --> ti.u32
    currentHouseholdSize=ti.u32,

    baseSocialFactor=ti.u8,
    socialFactor=ti.u8,

    incubationTimer=ti.u8,
    recoveryTimer=ti.u8)


def ResetTaichiFields(Cell, width, height, renderWidth, renderHeight):
    global erfolgreichInfiziert, gridAlt, grid, gridColorField, statePallete, renderColorField

    erfolgreichInfiziert = ti.field(dtype=ti.i32, shape=())

    gridAlt = Cell.field(shape=(width, height))
    grid = Cell.field(shape=(width, height))


    gridColorField = ti.Vector.field(3, dtype=ti.f32, shape=(height, width))
    statePallete = ti.Vector.field(3, dtype=ti.f32, shape=4)
    renderColorField = ti.Vector.field(3, dtype=ti.f32, shape=(renderWidth, renderHeight))

    print("Felder Definiert")


ResetTaichiFields(Cell, width, height, renderWidth, renderHeight)


#States
simulationRunning = False
mode = 0
setup = False

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
fünfHaushalt = 0
plusSechs = 0
haushaltFehler = False

#Konfigration der Zellen
demografie = np.array([], dtype=np.float32)
householdData = np.array([], dtype=np.float32)

startKranke = 0
socialInput = 0

window = ti.ui.Window("Zellautomat", res=(800, 800), vsync=False, fps_limit=5)
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
durchlauf = 0
maxDurchlauf = 0

# Debug-Zähler zur Diagnose der Ansteckungslogik
debugVersuche = ti.field(dtype=ti.i32, shape=())
debugErfolge = ti.field(dtype=ti.i32, shape=())

#Speichern/Laden
SpeicherDatei = "einstellungen.json"
statusMeldung = ""
statusMeldungTimer = 0
frameZaehler = 0


#==============
#Speichern / Laden
#===============

def SammleParameter():
    """Sammelt alle im GUI einstellbaren Parameter in einem Dictionary."""
    return {
        "width": width,
        "height": height,
        "maxDurchlauf": maxDurchlauf,

        "childDemo": childDemo,
        "adultDemo": adultDemo,
        "rentnerDemo": rentnerDemo,
        "ageFactor": ageFactor,
        "socialInput": socialInput,

        "einsHaushalt": einsHaushalt,
        "zweiHaushalt": zweiHaushalt,
        "dreiHaushalt": dreiHaushalt,
        "vierHaushalt": vierHaushalt,
        "fünfHaushalt": fünfHaushalt,
        "householdFactor": householdFactor,

        "startKranke": startKranke,
        "baseTransmissionrate": baseTransmissionrate,
        "mortalityrate": mortalityrate,
        "maxRadius": maxRadius,
        "incubationTime": incubationTime,
        "recoveryTime": recoveryTime,
    }


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
    global width, height, maxDurchlauf
    global childDemo, adultDemo, rentnerDemo, plusDemo, ageFactor, socialInput
    global einsHaushalt, zweiHaushalt, dreiHaushalt, vierHaushalt, fünfHaushalt, plusSechs, householdFactor
    global startKranke, baseTransmissionrate, mortalityrate, maxRadius, incubationTime, recoveryTime
    global demoFehler, haushaltFehler, statusMeldung, statusMeldungTimer

    try:
        if not os.path.exists(dateiname):
            statusMeldung = "Datei nicht gefunden: " + dateiname
            statusMeldungTimer = 120
            return

        with open(dateiname, "r", encoding="utf-8") as f:
            daten = json.load(f)

        width = int(daten.get("width", width))
        height = int(daten.get("height", height))
        maxDurchlauf = int(daten.get("maxDurchlauf", maxDurchlauf))

        childDemo = int(daten.get("childDemo", childDemo))
        adultDemo = int(daten.get("adultDemo", adultDemo))
        rentnerDemo = int(daten.get("rentnerDemo", rentnerDemo))
        ageFactor = int(daten.get("ageFactor", ageFactor))
        socialInput = int(daten.get("socialInput", socialInput))
        einsHaushalt = int(daten.get("einsHaushalt", einsHaushalt))
        zweiHaushalt = int(daten.get("zweiHaushalt", zweiHaushalt))
        dreiHaushalt = int(daten.get("dreiHaushalt", dreiHaushalt))
        vierHaushalt = int(daten.get("vierHaushalt", vierHaushalt))
        fünfHaushalt = int(daten.get("fünfHaushalt", fünfHaushalt))
        householdFactor = int(daten.get("householdFactor", householdFactor))



        startKranke = int(daten.get("startKranke", startKranke))
        baseTransmissionrate = int(daten.get("baseTransmissionrate", baseTransmissionrate))
        mortalityrate = int(daten.get("mortalityrate", mortalityrate))
        maxRadius = int(daten.get("maxRadius", maxRadius))

        incubationTime = int(daten.get("incubationTime", incubationTime))
        recoveryTime = int(daten.get("recoveryTime", recoveryTime))

        plusDemo = 100 - (childDemo + adultDemo + rentnerDemo)
        demoFehler = plusDemo < 0

        plusSechs = 100 - (einsHaushalt + zweiHaushalt + dreiHaushalt + vierHaushalt + fünfHaushalt)
        haushaltFehler = plusSechs < 0

        statusMeldung = "Geladen: " + dateiname
    except Exception as e:
        statusMeldung = "Fehler beim Laden: " + str(e)
    statusMeldungTimer = 120


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
def KrankheitsAusbruch(width: ti.i32, height: ti.i32, grid: ti.template(), erfolgreichInfiziert: ti.template(), startKranke: ti.i32):


    erfolgreichInfiziert[None] = 0
    versuche = 0
    maxVersuche = width * height * 20

    while erfolgreichInfiziert[None] < startKranke and versuche < maxVersuche:

        i = int(ti.random() * width)
        j = int(ti.random() * height)

        oldState = ti.atomic_max(grid[i, j].status, 1)

        if oldState == 0:
            ti.atomic_add(erfolgreichInfiziert[None], 1)

        versuche += 1


@ti.kernel
def InitializeAge(width: ti.i32, height: ti.i32, grid: ti.template(), demografie: ti.types.ndarray()):

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

        grid[i, j].age = generatedAge


@ti.kernel
def InitializeSocial(width: ti.i32, height: ti.i32, grid: ti.template(), socialInput: ti.i32):

    for i, j in ti.ndrange(width, height):
        age = ti.cast(grid[i, j].age, ti.f32)

        altersFaktor = ti.max(0.1, 1.0 - (ti.pow(age - 20.0, 2) / 5000.0))

        zufallsKontakte = ti.cast(socialInput * ti.random() * altersFaktor, ti.i32)

        grid[i, j].socialFactor = zufallsKontakte + grid[i, j].currentHouseholdSize


@ti.kernel
def InitializeHouseholds(width: ti.i32, height: ti.i32, grid: ti.template(), haushalteDaten: ti.types.ndarray()):
    for i, j in ti.ndrange(width, height):

        grid[i, j].householdID = i * height + j + 1
        grid[i, j].currentHouseholdSize = 1

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

        grid[i, j].maxHouseholdSize = hZahl


@ti.kernel
def CreateHouseholdsStep(width: ti.i32, height: ti.i32, grid: ti.template()):

    for i, j in ti.ndrange(width, height):

        if grid[i, j].currentHouseholdSize < grid[i, j].maxHouseholdSize:
            found = False

       
            for di in range(-1, 2):
                for dj in range(-1, 2):
                    if not found or (di != 0 or dj != 0):
                        ni = (i + di + width) % width
                        nj = (j + dj + height) % height

                        targetSingleID = ni * height + nj + 1

                        if grid[ni, nj].householdID == targetSingleID:

      
                            oldID = ti.atomic_min(grid[ni, nj].householdID, grid[i, j].householdID)

                            if oldID == targetSingleID:

                                if grid[ni, nj].householdID == grid[i, j].householdID:
                                    grid[i, j].currentHouseholdSize += 1
                                    found = True


@ti.kernel
def Calculation(width: ti.i32, height: ti.i32, grid: ti.template(), gridAlt: ti.template(), baseTransmissionrate: ti.f32, householdFactor: ti.i32, mortalityRate: ti.f32, ageFactor: ti.i32, incubationTime: ti.i32, recoveryTime: ti.i32, maxRadius: ti.i32, debugVersuche: ti.template(), debugErfolge: ti.template()):

    for i, j in ti.ndrange(width, height):

        if gridAlt[i, j].status == 1:

            hatSymptome = gridAlt[i, j].recoveryTimer > 0

            kontakte = 0
            suchRadius = 0

            if hatSymptome:
                kontakte = gridAlt[i, j].currentHouseholdSize
                suchRadius = 2
            else:
                kontakte = gridAlt[i, j].socialFactor
                suchRadius = ti.cast(kontakte / 2, ti.i32)

            anzahlSuchen = 0
            cellAlter = gridAlt[i, j].age

            for di in range(-maxRadius, maxRadius + 1):
                for dj in range(-maxRadius, maxRadius + 1):

                    if anzahlSuchen < kontakte and ti.abs(di) <= suchRadius and ti.abs(dj) <= suchRadius:
                        if di != 0 or dj != 0:

                            ni = (i + di + width) % width
                            nj = (j + dj + height) % height

                            istGleicherHaushalt = gridAlt[ni, nj].householdID == gridAlt[i, j].householdID

                            if not(hatSymptome) or (hatSymptome and istGleicherHaushalt):
                                anzahlSuchen += 1

                                if gridAlt[ni, nj].status == 0:
                                    ti.atomic_add(debugVersuche[None], 1)

                                    currentTransmissionrate = baseTransmissionrate

                                    if istGleicherHaushalt:
                                        currentTransmissionrate = baseTransmissionrate * ti.cast(householdFactor, ti.f32)

                                    if ti.random() <= currentTransmissionrate:
                                        ti.atomic_add(debugErfolge[None], 1)
                                        ti.atomic_max(grid[ni, nj].status, 1)

  

            gesammteKrankheitsdauer = incubationTime + recoveryTime
            gesammtRisikoZelle = mortalityRate * ((ti.cast(cellAlter, ti.f32) / 90.0) * ti.cast(ageFactor, ti.f32))
            gesammtRisikoZelle = ti.max(0.0, ti.min(gesammtRisikoZelle, 0.9999))
            taeglicheSterbechance = 1.0 - ti.pow(1.0 - gesammtRisikoZelle, 1.0 / ti.cast(gesammteKrankheitsdauer, ti.f32))

            if ti.random() <= taeglicheSterbechance:
                grid[i, j].status = 3
            else:

                if gridAlt[i, j].recoveryTimer >= recoveryTime:
                    grid[i, j].recoveryTimer = 0
                    grid[i, j].status = 2

                elif hatSymptome:
                    grid[i, j].recoveryTimer = gridAlt[i, j].recoveryTimer + 1

                elif gridAlt[i, j].incubationTimer >= incubationTime:
                    grid[i, j].incubationTimer = 0
                    grid[i, j].recoveryTimer = 1

                else:
                    grid[i, j].incubationTimer = gridAlt[i, j].incubationTimer + 1


@ti.kernel
def ColorCells(width: ti.i32, height: ti.i32, grid: ti.template(), gridColorField: ti.template(), statePallete: ti.template()):
    for i, j in ti.ndrange(width, height):
        cellAge = grid[i, j].age


        helligkeit = 1.0 - (ti.cast(cellAge, ti.f32) / 90.0) * 0.5

        gridColorField[j, width - i - 1] = statePallete[grid[i, j].status] * helligkeit



#Debugging
@ti.kernel
def ZaehleStatus(width: ti.i32, height: ti.i32, grid: ti.template()) -> tm.ivec4:
    counts = tm.ivec4(0, 0, 0, 0)
    for i, j in ti.ndrange(width, height):
        status_idx = ti.cast(grid[i, j].status, ti.i32)
        counts[status_idx] += 1
    return counts


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
#Simulation
#===========================
    if simulationRunning:
        with gui.sub_window("Simulation", x=0, y=0, width=0.3, height=0.25):

            if gui.button("Stop"):
                simulationRunning = False

        if setup:

            InitializePallets(statePallete)

            startKrankeSicher = min(startKranke, width * height)
            KrankheitsAusbruch(width, height, grid, erfolgreichInfiziert, startKrankeSicher)

            InitializeAge(width, height, grid, demografie)

            InitializeHouseholds(width, height, grid, householdData)

            InitializeSocial(width, height, grid, socialInput)

            for i in range(10):
                CreateHouseholdsStep(width, height, grid)

            setup = False
            print(grid.shape)

        gridAlt.copy_from(grid)

        debugVersuche[None] = 0
        debugErfolge[None] = 0
        Calculation(width, height, grid, gridAlt, baseTransmissionrate * 0.01, householdFactor, mortalityrate * 0.01, ageFactor, incubationTime, recoveryTime, maxRadius, debugVersuche, debugErfolge)

        ColorCells(width, height, grid, gridColorField, statePallete)
        BildRunterskallieren(width, height, renderWidth, renderHeight, gridColorField, renderColorField)


        frameZaehler += 1
        counts = ZaehleStatus(width, height, grid)
        print(f"Frame {frameZaehler} | Gesund: {counts[0]}  Krank: {counts[1]}  Immun: {counts[2]}  Tot: {counts[3]}  |  Versuche: {debugVersuche[None]}  Erfolge: {debugErfolge[None]}")


#==================================
#Hauptmenü  logik
#===================================

    else:
        # Allgemein ------------------
        with gui.sub_window("Hauptmenü", x=0, y=0, width=0.3, height=0.45):

            if gui.button("Allgemein"):
                mode = 3
            if gui.button("Demografie"):
                mode = 1
            if gui.button("Haushalte"):
                mode = 2
            if gui.button("Krankheit"):
                mode = 4
            gui.text("")

            #Start Button --------------------
            if demoFehler == False and haushaltFehler == False:
                if gui.button("Start"):

                    demografie = np.array([childDemo, adultDemo, rentnerDemo, plusDemo], dtype=np.float32) * 0.01
                    householdData = np.array([einsHaushalt, zweiHaushalt, dreiHaushalt, vierHaushalt, fünfHaushalt, plusSechs], dtype=np.float32) * 0.01

                    ResetTaichiFields(Cell, width, height, renderWidth, renderHeight)

                    simulationRunning = True
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

            if statusMeldungTimer > 0:
                gui.text(statusMeldung)

        # Demografie----------------
        if mode == 1:
            with gui.sub_window("Demografie", x=0.3, y=0., width=0.5, height=0.4):
                gui.text("0 - 19")

                childDemo = gui.slider_int("%", childDemo, 0, 100)

                gui.text("20 - 64")
                adultDemo = gui.slider_int("% ", adultDemo, 0, 100)



                gui.text("65 - 79")
                rentnerDemo = gui.slider_int("%  ", rentnerDemo, 0, 100)

                gui.text("80+")
                plusDemo = 100 - (childDemo + adultDemo + rentnerDemo)

                if plusDemo < 0:
                    gui.text("!!! " + str(plusDemo) + " !!!")
                    demoFehler = True
                else:
                    demoFehler = False
                    gui.text(str(plusDemo))



                gui.text("Altersfaktor")
                ageFactor = gui.slider_int(" ", ageFactor, 0, 10)

                gui.text("Maximale Anzahl Freunde")
                socialInput = gui.slider_int("", socialInput, 0, 20)

        if mode == 2:

            with gui.sub_window("Haushalte", x=0.3, y=0., width=0.5, height=0.4):
                gui.text("1 Person")
                einsHaushalt = gui.slider_int("%", einsHaushalt, 0, 100)

                gui.text("2 Personen")
                zweiHaushalt = gui.slider_int("% ", zweiHaushalt, 0, 100)

                gui.text("3 Personen")
                dreiHaushalt = gui.slider_int("%   ", dreiHaushalt, 0, 100)

                gui.text("4 Personen")
                vierHaushalt = gui.slider_int("%    ", vierHaushalt, 0, 100)


                gui.text("5 Personen")
                fünfHaushalt = gui.slider_int("%     ", fünfHaushalt, 0, 100)


                plusSechs = 100 - (einsHaushalt + zweiHaushalt + dreiHaushalt + vierHaushalt + fünfHaushalt)


                if plusSechs < 0:
                    gui.text("!!! " + str(plusSechs) + " !!!")
                    haushaltFehler = True
                else:
                    haushaltFehler = False
                    gui.text(str(plusSechs))

                gui.text("Haushaltsfaktor")
                householdFactor = gui.slider_int("", householdFactor, 0, 10)

        if mode == 3:
            with gui.sub_window("Allgemein", x=0.3, y=0., width=0.5, height=0.4):

                gui.text("Höhe")
                height = gui.slider_int("", height, 1, maxHeight)

                gui.text("Breite")
                width = gui.slider_int(" ", width, 1, maxWidth)


                gui.text("Anzahl Zellen: " + str(height * width))

                gui.text("Anzahl Tage")
                maxDurchlauf = gui.slider_int("  ", maxDurchlauf, 0, 100)

        if mode == 4:
            with gui.sub_window("Krankheit", x=0.3, y=0., width=0.5, height=0.5):


                gui.text("Infizierte am Anfang")
                startKranke = gui.slider_int("", startKranke, 0, maxHeight)
                gui.text("(wird auf Zellenzahl gedeckelt)")


                gui.text("Übertragungsrate")
                baseTransmissionrate = gui.slider_int(" ", baseTransmissionrate, 0, 100)

                gui.text("Tödlichkeitsrate")
                mortalityrate = gui.slider_int("  ", mortalityrate, 0, 100)

                gui.text("Max. Ansteckungsradius")
                maxRadius = gui.slider_int("   ", maxRadius, 1, 15)

                gui.text("Inkubationszeit (Tage)")
                incubationTime = gui.slider_int("    ", incubationTime, 1, 30)

                gui.text("Genesungszeit (Tage)")
                recoveryTime = gui.slider_int("     ", recoveryTime, 1, 30)

    canvas.set_image(renderColorField)
    window.show()