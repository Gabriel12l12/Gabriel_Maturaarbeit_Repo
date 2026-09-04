#  -*- coding: cp1252 -*-
import taichi as ti
import numpy as np

seed = 123
ti.init(arch=ti.gpu, random_seed=seed)

N = 10
field1 = ti.field(ti.i32, shape=N)
field2 = ti.field(ti.i32, shape=N)

field1.from_numpy(np.zeros(N, dtype=np.int32))
field2.from_numpy(np.zeros(N, dtype=np.int32))



@ti.func
def zufallszahlen_generieren(f1: ti.template(), f2: ti.template()):

    for i in f1:
        f1[i] = ti.abs(ti.random(ti.i32)) % 10
        
    for i in f2:
        f2[i] = ti.abs(ti.random(ti.i32)) % 10

@ti.kernel
def Abgleichen(f1: ti.template(), f2: ti.template(), index: ti.i32) -> ti.i32:
    gleich = 0 
    zufallszahlen_generieren(f1, f2)
    
    for i in range(index):
        if f2[i] == f1[i]:
            gleich += 1 

    return gleich

ergebniss = Abgleichen(field1, field2, N)
print("Es hat: ", str(ergebniss), " gleiche Zahlen")
