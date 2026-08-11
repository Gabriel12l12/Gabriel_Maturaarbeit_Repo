#  -*- coding: cp1252 -*-
#Zeile 1 wird geschrieben, um Umlaute (ä, ö, ü) beim Kommentieren verwenden zu können
#Importieren der verwendeten Python Bibliotheken:
import pygame #Bibliothek um das Fenster anzuzeigen
import random # Bibliothek um Zufallsoperationen zu ermöglichen

pygame.init() # initialisierung von Pygame

#Definierung einiger Konstanten (bsp. Farben)
BLACK = (0,0,0)
GREY =  (128,128,128)
YELLOW = (255,255,0)

WIDTH, HEIGHT = 800,800 #Grösse des Fensters
TILE_SIZE = 20 #Grösse der Zellen
GRID_WIDTH = WIDTH // TILE_SIZE #Breite der Zelle (Bestimmt die vertikalen Gitterlinien)
GRID_HEIGHT = HEIGHT // TILE_SIZE #Höhe der Zelle (Bestimmt die horizontalen Gitterlinien)
FPS = 60 #Frames per second

#Erstellen eines Fensters
screen = pygame.display.set_mode((WIDTH,HEIGHT))


clock = pygame.time.Clock() #Variable um Geschwindigkeit der Berechnungen des Programmes zu regeln

#Funktion um zufällige Zellenpositionen zu wählen (an diesen Stellen werden die Zellen lebendig)
def Gen(num):
    return set( [   (random.randrange(0, GRID_HEIGHT), random.randrange(0, GRID_WIDTH)) for i in range(num)]   ) #Es wird num (random.randrange(2,5)*GRID_WIDTH) mal eine zufällige Position generiert


def Draw_grid(positions):
    for position in positions: #Jede lebendige Zelle wird durchgegangen
        col, row = position #Position der Zelle wird aufgespalten (col = x-Koordinate; row = Y-Koordinate)
        top_left = (col * TILE_SIZE, row * TILE_SIZE) #Obere linke Ecke der würfelförmigen Zelle wird ermittelt (also ein Punkt)
        pygame.draw.rect(screen, YELLOW, (*top_left, TILE_SIZE, TILE_SIZE)) #Zelle wird ausgehend von der oberen linken Ecke mit der Farbe YELLOW gezeichnet

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

            neighbors.append((x + dx, y + dy)) #Die Nachbarszelle wird in die Liste eingefügt

    return neighbors
#Warum funktioniert [-1, 0, 1]? Das geht, weil man damit perfekt alle Zellen um die lebendige Zelle herum erfassen kann, da:
                                    #[3][6][9]      [-1, 1][ 0, 1][ 1, 1]
                                    #[2][X][8]  =   [-1, 0][Zelle][ 1, 0]
                                    #[1][4][7]      [-1,-1][ 0,-1][ 1,-1] und die For-Schleife all diese Kombinationen durchgeht. 
                                                                        #Die linke Matrix zeigt die Reihenfolge der kontrolierten Zellen an

def Adjust_grid(positions):
    all_neighbors = set() #Alle benachbarten Zellen VOR dem Update werden in diesem Set gespeichert
    new_positions = set() #Die Positionen von den neuen Zellen, also NACH dem Update, werden hier gespeichert

    for position in positions: #Die Schleife geht durch alle lebendigen Zellen durch
        neighbors = Get_neighbors(position) #Alle Nachbarn von der Zelle des jetzigen For-Durchlaufes werden in der Variable gespeichert
        all_neighbors.update(neighbors) #Alle Nachbarn aus der neighbors-Variable werden in das Set all_neighbors koppiert/übertragen

        neighbors = list(filter(lambda x: x in positions, neighbors )) #Alle toten Nachbarn werden rausgefiltert 
        #lambda dient als Filterfunktion, welche dann neighbors durchgeht (es schaut nach, ob die Zelle in positions erwähnt wird; nein = tot = rausgefiltert). filter() gibt einen Iterator zurueck, welchen wir in eine Liste konvertieren

        if len(neighbors) in [2,3]: #Wenn die Zelle 2 oder 3 lebendige Nachbarn besitzt :
            new_positions.add(position) #Wird diese zu new_positions übertragen (bleibt also am leben, sind KEINE neuen Zellen)

    for position in all_neighbors: #Geht alle erfassten Nachbarzellen durch
        neighbors = Get_neighbors(position) #Ermittelt alle Nachbarzellen (also 2.Grades) der Nachbarzellen (1.Grades)
        neighbors = list(filter(lambda x: x in positions, neighbors )) #Filtert alle toten Nachbarzellen 2.Grades raus

        if len(neighbors) == 3: #Wenn die Nachbarzelle 3 Nachbarn hat:
            new_positions.add(position) #Wird diese zu new_positions übertragen (Das sind neue Zellen)

    #Alle Zellen, mit zuvielen oder zuwenigen Nachbarn werden nie nach new_positions übertragen, was bedeutet, das diese nach dem Update nicht leben

    return new_positions #Alle Zellen, die NACH dem Update noch am leben sind werden zurück gegeben


#Hauptfunktion
def Main():
    running = True
    playing = False

    count = 0
    update_freq = 10 #Variable um die Updategeschwindigkeit zu kontrollieren (desto kleiner desto schneller)

    positions = set() #Variable um alle einzelnen Lebendigen Zellen zu speichern

    #Hauptschleife
    while running:
        clock.tick(FPS) #Regulierung der Berechnungsgeschwindigkeit

        if playing: #Nur wenn man im SPielen-Modus ist, wird gezählt, sodass keine Updates während Pause gedrückt ist passieren
            count += 1

        #Updaten der Zellen
        if count >= update_freq: 
            count = 0 #Neuer Updatecyklus beginnt
            positions = Adjust_grid(positions) #Geupdatete Zellen werden auf den "Zellenspeicher" übertragen

        pygame.display.set_caption("Playing" if playing else "Paused") #Momentaner Modus wird im Fensternamen beschrieben (also ob z.B pausiert ist)

        for event in pygame.event.get(): #Listet alle Events von pygame auf, welche passiert sind (in der Warteschlange stehen, verarbeitet zu werden)

            if event.type == pygame.QUIT: #Wird ausgeführt, wenn man den X Knopf oben rechts am Fenster drückt
                running = False #Hauptschleife wird beendet

            if event.type == pygame.MOUSEBUTTONDOWN: #Kontrolliert, ob ein Mausinput passiert ist (egal was für einer)
                x,y = pygame.mouse.get_pos() #Position des clicks wird ermittelt
                #X und Y Koordinaten des Klicks werden einzeln durch die Zellengrösse geteilt und zusammengesetzt(um zu ermitteln, welche Zelle angeklickt wurde)
                col = x// TILE_SIZE
                row = y // TILE_SIZE
                pos = (col, row) 

                if pos in positions: #Wenn man auf eine Zelle klickt, welche schon gelb/lebendig war, ist sie dies nicht mehr
                    positions.remove(pos)
                else:
                    positions.add(pos) #Hier passiert das umgekehrte, die Zelle wird gelb/lebendig
                
            if event.type == pygame.KEYDOWN: #Registrierung von Tasteninputs (allgemein)
                if event.key == pygame.K_SPACE: # Kontrollieren, ob leertaste/Space gedrückt wurde
                    playing = not playing #Pausieren durch veränderung der Variable

                if event.key == pygame.K_c: # Kontrollieren, ob C gedrückt wurde
                    positions = set() #positions wird geleert, alle Zellen sind Tot/ Spielefläche ist wieder frei
                    playing = False #Spiel wird pausiert
                    count = 0 #Damit der Wechsel von Pause zu SPielen sich nicht komisch anfühlt, wird der Updatecyklus resetet

                if event.key == pygame.K_g: # Kontrollieren, ob G gedrückt wurde
                    positions = Gen(random.randrange(2,5) * GRID_WIDTH) #Generieren eine zufällige Anzahl zufälliger Zellen (GRID_WIDTH ist vom Tutorial-Ersteller willkürlich gewählt, kann man auch weglassen)

        screen.fill(GREY) # Hintergrund des Fensters
        Draw_grid(positions) #Gitterlinien werden gezeichnet
        pygame.display.update() # Alle veränderungen werden aufs Fenster übertragen

    pygame.quit() #Damit keine Berechnungen im Hintergrund passieren obwohl das Fenster geschlossen ist, wird das Programm zusätzlich hier nochmals beendet

Main() #Aufrufen der Hauptfunktion