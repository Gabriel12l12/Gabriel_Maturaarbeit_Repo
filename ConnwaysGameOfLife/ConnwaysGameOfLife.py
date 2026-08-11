#  -*- coding: cp1252 -*-
import pygame
import random 
import numpy as np
import matplotlib.pyplot as plt 

pygame.init() 

BLACK = (0,0,0)
GREY =  (128,128,128)
YELLOW = (255,255,0)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)

WIDTH, HEIGHT = 800,800 #Grösse des Fensters
TILE_SIZE = 20 #Grösse der Zellen
GRID_WIDTH = WIDTH // TILE_SIZE #Breite der Zelle (Bestimmt die vertikalen Gitterlinien)
GRID_HEIGHT = HEIGHT // TILE_SIZE #Höhe der Zelle (Bestimmt die horizontalen Gitterlinien)
FPS = 60 #Frames per second

screen = pygame.display.set_mode((WIDTH,HEIGHT))
clock = pygame.time.Clock()

def cellPlotAnim(ax, line_sick,line_immune,x_value,y_valueSick, y_valueImmune):
      line_sick.set_data(x_value, y_valueSick)
      line_immune.set_data(x_value, y_valueImmune)

      ax.relim()
      ax.autoscale_view()

      plt.draw()
      plt.pause(0.001)
    
def countCells(all_cells):
    sick =0
    immune = 0
    for cell in all_cells:
        if all_cells[cell][0] == "sick":
            sick += 1
        else:
            immune += 1
    return sick,immune

def Draw_grid(all_cells):
    for position in all_cells: #Jede lebendige Zelle wird durchgegangen
        col, row = position #Position der Zelle wird aufgespalten (col = x-Koordinate; row = Y-Koordinate)
        top_left = (col * TILE_SIZE, row * TILE_SIZE) #Obere linke Ecke der würfelförmigen Zelle wird ermittelt (also ein Punkt)
        if all_cells[position][0] == "immune":
            colour = BLUE
        else:
            colour = YELLOW
        pygame.draw.rect(screen, colour, (*top_left, TILE_SIZE, TILE_SIZE)) 

    #Horizontalen Gitterlinien werden gezeichnet anhand der Zell- und Bildschirmgrösse
    for row in range(GRID_WIDTH):
        pygame.draw.line(screen, BLACK, (0,row*TILE_SIZE), (WIDTH, row * TILE_SIZE))

    #Vertikale Gitterlinien werden gezeichnet anhand der Zell- und Bildschirmgrösse
    for col in range(GRID_HEIGHT):
        pygame.draw.line(screen, BLACK, (col*TILE_SIZE,0), (col * TILE_SIZE, HEIGHT))


def Get_neighbors(pos):
    x,y = pos #Die x und y Koordinaten der Zelle werden aufgespalten in die Variabeln x (für x-Koordinate) und y (für die y-Koordinate)
    neighbors =[] #Liste, in welcher alle Nachbarszellen gespeichert werden

    for dx in [-1, 0, 1]:
        if x + dx < 0 or x + dx > GRID_WIDTH: #Ist die benachbarte Zelle links oder rechts ausserhalb des sichtbaren Fensters
            continue     #Überspringe diese Zelle

        for dy in [-1, 0, 1]:
            if y + dy < 0 or y + dy > GRID_HEIGHT: #Ist die Zelle oberhalb oder unterhalb des sichtbaren Fensters:
                continue #Überspringe diese Zelle

            if dx == 0 and dy == 0: #Überspringt die Zelle,wessen Nachbarn man zählen will(du bist ja nicht dein eigener Nachbar)
                continue

            neighbors.append((x + dx, y + dy)) #Die Nachbarszelle wird in die Liste eingefuegt

    return neighbors


def Adjust_grid(all_cells):
    all_neighbors = set()
    update = {} 

    for cell in all_cells:
        if all_cells[cell][0] == "immune":
            update[cell] = ["immune"]
        else:
            neighbors = Get_neighbors(cell)
            all_neighbors.update(neighbors) 
            update[cell] = ["immune"] 

    for neighbor in all_neighbors:
        if not neighbor in all_cells:
            update[neighbor] = ["sick"] 
    
    return update 

def Gen(num):
    return set( [   (random.randrange(0, GRID_HEIGHT), random.randrange(0, GRID_WIDTH)) for i in range(num)]   )

#Hauptfunktion
def Main():
    running = True
    playing = False

    count = 0
    updateCount = 0
    update_freq = 10 
    all_cells = {} 

    plt.ion()
    fig, ax = plt.subplots()
    (line_sick,) = ax.plot([], [], "b-", label="Krank")
    (line_immune,) = ax.plot([], [], "r-", label="Immun")
    x_value = [0]
    y_valueSick = [0]
    y_valueImmune = [0]

    #Hauptschleife
    while running:
        clock.tick(FPS) 

        if playing: 
            count += 1

        #Updaten der Zellen
        if count >= update_freq: 
            count = 0 
            all_cells = Adjust_grid(all_cells) 
            updateCount += 1
            sick, immune = countCells(all_cells)

            x_value.append(updateCount)
            y_valueSick.append(sick)
            y_valueImmune.append(immune)

            cellPlotAnim(ax, line_sick,line_immune,x_value,y_valueSick, y_valueImmune)

        pygame.display.set_caption("Playing" if playing else "Paused") 

        for event in pygame.event.get(): #Listet alle Events von pygame auf, welche passiert sind (in der Warteschlange stehen, verarbeitet zu werden)

            if event.type == pygame.QUIT: #Wird ausgeführt, wenn man den X Knopf oben rechts am Fenster drückt
                running = False #Mainschleife wird beende

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    x,y = pygame.mouse.get_pos() #Position des clicks wird ermittelt
                    #X und Y Koordinaten des Klicks werden einzeln durch die Zellengrösse geteilt und zusammengesetzt(um zu ermitteln, welche Zelle angeklickt wurde)
                    col = x// TILE_SIZE
                    row = y // TILE_SIZE
                    pos = (col, row) 

                    if pos in all_cells and all_cells[pos][0] == "immune": 
                        all_cells.pop(pos)
                    else:
                        all_cells[pos] = ["immune"]
                else:
                    x,y = pygame.mouse.get_pos()
                    col = x// TILE_SIZE
                    row = y // TILE_SIZE
                    pos = (col, row) 

                    if pos in all_cells: 
                        all_cells.pop(pos)
                    else:
                        all_cells[pos] = ["sick"]
                
            if event.type == pygame.KEYDOWN: #Registrierung von Tasteninputs (allgemein)
                if event.key == pygame.K_SPACE: # Kontrollieren, ob leertaste/Space gedrückt wurde
                    playing = not playing #Pausieren durch veränderung der Variable

                if event.key == pygame.K_c: # Kontrollieren, ob C gedrückt wurde
                    all_cells = {} #all_cells wird geleert, alle Zellen sind Tot/ Spielefläche ist wieder frei
                    playing = False #Spiel wird pausiert
                    count = 0 

                if event.key == pygame.K_g: 
                    all_cells = Gen(random.randrange(2,5) * GRID_WIDTH) 
        screen.fill(GREY) 
        Draw_grid(all_cells) 
        pygame.display.update() 
    pygame.quit() 

Main()