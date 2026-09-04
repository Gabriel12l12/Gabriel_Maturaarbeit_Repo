import numpy as np
import taichi as ti


ti.init(arch=ti.gpu) 

res = (800,800)

window = ti.ui.Window("Set Immage", res, vsync=True)
canvas = window.get_canvas()
gui = window.get_gui()

N = res[0]

vectorField = ti.Vector.field(3, ti.f32, (N, N))


@ti.kernel
def Kernel1(col: ti.types.ndarray(), row: ti.types.ndarray()):

    for x in col:
        for y in row:
            vectorField[x,y] = ti.Vector([float(25) / 25.0, float(0) / 25.0, float(0) / 25.0], ti.f32)



@ti.kernel
def Kernel2(col: ti.types.ndarray(), row: ti.types.ndarray()):
    for x in col:
        for y in row:
            vectorField[x,y] = ti.Vector([float(0) / 25.0, float(25) / 25.0, float(0) / 25.0], ti.f32)
    

def main():
    

    row = np.zeros(shape = N, dtype = np.int32)
    col = np.zeros(shape = N, dtype = np.int32)
    
    for i in range(N):
        row[i] = i
        col[i] = i



    w = 0

    while window.running:
        if w == 200:
            Kernel1(col, row)
            w = 0
        elif w == 100:
            Kernel2(col,row)
        w += 1
        canvas.set_image(vectorField)
        window.show()
 





main()

