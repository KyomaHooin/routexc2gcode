#!/usr/bin/python3
# Tento program jest svobodný software a je prevodnikem routovaciho excellonu do G-code (beznych frezek)
# autor: Vladimir Cerny
# email: cernyv.pdp7@gmail.com
# licence GPLv3
# verze 1.1

import os
import datetime

# definice promennych

dir = "D:/cnc"
print("Vychozi cesta zdroje D:\\cnc")
zdrojovy = input("Zadej nazev zdrojoveho souboru: ")
cela_cesta_vstupu = os.path.join(dir,zdrojovy)
dir2 = "D:/cnc/gcode"
print("Vychozi cesta cile D:\\cnc\\gcode", "Existujici soubory prepise!", sep=os.linesep)
vystupni = input("Zadej nazev vystupniho souboru: ")
cela_cesta_vystupu = os.path.join(dir2,vystupni)
otacky = input("Zadej otacky vretene, [vychozi 20000]: ") or "20000"
feedrate = input("Zadej feedrate, [vychozi F300]: ") or "F300"
moveZ = input("Zadej vysku prejezdu nad DPS, [vychozi 5]: ") or "5"
milldepth = input("Zadej hloubku frezovani, [vychozi -2]: ") or "-2"
nastroj_c = input("Zadej cislo nastroje, [vychozi 1]: ") or "1"
safeZ = input("Zadej vysku zvednuti Z na konci programu, [vychozi 40]: ") or "40"
today = datetime.datetime.now()

# urceni vystupniho souboru

out = open(f"{cela_cesta_vystupu}", "w")

out.write("; "+f"{today}\n")

hlavicka = """; Generovano v routexc2gcode.py

; Vyber nastroj
T"""+str(nastroj_c)+"""M6
; Spust vreteno
S"""+str(otacky)+"""M3
; Zvednuti Z po startu
G00 Z5
"""

paticka = """
; zastav vreteno
M5
; vyjeti vretene a konec frezovani
G00 Z"""+str(safeZ)+"""
; konec programu
M2
"""

# zapis hlavicky
out.write(hlavicka)

# pohyb vretene
# moveZ ekvivaletni k M16 v exellonu
# M15 se vyjadri, G00 nasleduje G01 se stejnou souradnici a pohybem Z dolu (obvykle)

with open(f"{cela_cesta_vstupu}") as f:
  line = f.readline()
  while line:
    line = f.readline()
    if line.startswith("G00"):
      out.write(line)
      out.write("G01"+line.strip()[3:]+"Z"+milldepth+feedrate+"\n")
    if line.startswith("G01"):
      out.write(line[3:])
    if line.startswith(("X","Y")):
      out.write(line)
    #if line.startswith("M15"):
      #print(milldepth, "; Vreteno dolu")
      #milldepth = "Z-2"
    if line.startswith("M16"):
      out.write("Z"+moveZ+" "+"; Vreteno nahoru\n")
    #if line.startswith("G40"):
    #  print(line.strip())
    if line.startswith("M30"):
      break
f.close()

# zapis paticky
out.write(paticka)

# uzavreni vystupu
out.close()

print("Hotovo...")
