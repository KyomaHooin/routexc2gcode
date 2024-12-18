#!/usr/bin/python3
# Tento program jest svobodný software a je prevodnikem routovaciho excellonu do G-code (beznych frezek)
# autor: Vladimir Cerny
# email: cernyv.pdp7@gmail.com
# licence GPLv3

import os

# definice promennych

dir = "D:/cnc"
print("Vychozi cesta D:\\cnc")
zdrojovy = input("Zadej nazev zdrojoveho souboru: ")
cela_cesta = os.path.join(dir,zdrojovy)
vystupni = input("Zadej nazev vystupniho souboru: ")
otacky = input("Zadej otacky vretene, [vychozi 25000]: ") or "25000"
feedrate = input("Zadej feedrate, [vychozi F300]: ") or "F300"
safeZ = "40"
moveZ = "Z5"
milldepth = input("Zadej hloubku frezovani, [vychozi -2]: ") or "-2"
nastroj_c = input("Zadej cislo nastroje, [vychozi 1]: ") or "1"

# urceni vystupniho souboru

out = open(f"{vystupni}", "w")

hlavicka = """; Generovano v routexc2gcode.py

; Absolutni koordinaty
G90
; Metricke
G21
; Spust vreteno
M3 S"""+str(otacky)+"""
; Vyber nastroj
T0"""+str(nastroj_c)+"""
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

with open(f"{cela_cesta}") as f:
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
      out.write(moveZ+" "+"; Vreteno nahoru\n")
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
