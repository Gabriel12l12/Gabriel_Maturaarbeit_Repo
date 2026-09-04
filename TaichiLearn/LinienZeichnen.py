#  -*- coding: cp1252 -*-
import numpy as np
import taichi as ti

ti.init(arch=ti.gpu) 

res = (800, 800)

maxLines = 1000
maxCircles = 1000

lineField = ti.Vector.field(2, ti.f32, shape=maxLines * 2)
lineConnections = ti.field(ti.i32, shape=maxLines * 2)
width = 0.01

circleField = ti.Vector.field(2, ti.f32, shape = maxCircles)
radius = 0.5

@ti.kernel
def LineKernel(mousePos: ti.types.ndarray(), length: ti.i32):

    v0 = length * 2
    v1 = length * 2 + 1

    lineField[v0] = ti.Vector([mousePos[0], mousePos[1]])
    lineField[v1] = ti.Vector([mousePos[2], mousePos[3]])

    lineConnections[v0] = v0
    lineConnections[v1] = v1


@ti.kernel
def CircleKernel(mousePos: ti.types.ndarray(), length: ti.i32):
    circleField[length] = ti.Vector([mousePos[0], mousePos[1]])


def Main(width, radius):
    window = ti.ui.Window("Zeichnen", res)
    canvas = window.get_canvas()
    
    mouseLinePos = np.array([], dtype=np.float32)
    mouseCirclePos = np.array([], dtype = np.float32)

    lineColor = (1.0, 0.0, 0.0)
    circleColor = (1.0, 1.0, 0.0)
    
    line_count = 0  
    circleCount = 0

    mode = 0

    while window.running:
        gui = window.get_gui()

        #UI -----------------
        with gui.sub_window("Options", x=0.05, y=0.05, width=0.3, height=0.25):
            
            if gui.button("Line"): mode = 0
            width = gui.slider_float("Line Width", width, 0.001, 1)
            lineColor = gui.color_edit_3("Line Color", lineColor)

            if gui.button("Circle"):mode = 1
            radius = gui.slider_float("Circle Radius", radius, 0.001, 1)
            circleColor = gui.color_edit_3("Circle Color", circleColor)

            if gui.button("Clear Canvas"):
                mouseLinePos = np.array([], dtype=np.float32)
                mouseCirclePos = np.array([], dtype = np.float32)

                lineField.fill(0)
                circleField.fill(0)

                lineConnections.fill(0)

                lineCount = 0  
                cricleCount = 0
                print("Clear Canvas")

        #Linien Mode--------------
        if mode == 0:
            if window.get_event(ti.ui.PRESS):
                if window.event.key == ti.ui.LMB or window.event.key == ti.ui.RMB:
                    currentMousePos = window.get_cursor_pos()
                    mouseLinePos = np.append(mouseLinePos, currentMousePos[0])
                    mouseLinePos = np.append(mouseLinePos, currentMousePos[1])

                    listLength = len(mouseLinePos)
                    print(mouseLinePos)

                    if listLength % 4 == 0 and line_count < maxLines:
                        latestLinePoints = mouseLinePos[-4:].astype(np.float32)
                        LineKernel(latestLinePoints, listLength)
                        line_count += 1 

        if mode == 1:
            if window.get_event(ti.ui.PRESS):
                if window.event.key == ti.ui.LMB or window.event.key == ti.ui.RMB:
                    currentMousePos = window.get_cursor_pos()
                    
                    mouseCirclePos = np.append(mouseCirclePos, currentMousePos[0])
                    mouseCirclePos = np.append(mouseCirclePos, currentMousePos[1])

                    print("Mouse Pos", mouseCirclePos)

                    listLength = len(mouseCirclePos)
                    latestCirclePoints = mouseCirclePos[-2:].astype(np.float32)
                    print(listLength)

                    CircleKernel(latestCirclePoints, listLength)
  

        if line_count > 0:
            canvas.lines(lineField, width=width, indices=lineConnections, color=lineColor)

        canvas.circles(circleField, radius, circleColor)
            
        window.show()


Main(width, radius)

