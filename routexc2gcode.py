#!/usr/bin/python3
#
# Převodník routovacího Excellonu do G-code (běžných frézek)
#
#   autor: Vladimir Cerny
#   email: cernyv.pdp7@gmail.com
# licence: GPLv3
#   verze: 1.1
#

import os,sys
import datetime

#
# Promenne
#

cesta_vstupu = "D:/cnc"
cesta_vystupu = "D:/cnc/gcode"

today = datetime.datetime.now()

#
# Inicializace
#

print("\nroutexc2gcode\n")

print("Adresář zdroje [" + cesta_vstupu + "]\n")

zdrojovy_soubor = input("[*] Název zdrojového souboru: ")
cela_cesta_vstupu = os.path.join(cesta_vstupu, zdrojovy_soubor)

print("\nAdresář cíle [" + cesta_vystupu + "]\n")

vystupni = input("[*] Název výstupního souboru: ")
cela_cesta_vystupu = os.path.join(cesta_vystupu, vystupni)

otacky = input("\n[*] Otáčky vřetene [20000]: ") or "20000"
feedrate = input("[*] Feedrate [F300]: ") or "F300"
moveZ = input("[*] Výška přejezdu nad DPS [5]: ") or "5"
milldepth = input("[*] Hloubka frézování [-2]: ") or "-2"
nastroj_c = input("[*] Číslo nástroje [1]: ") or "1"
safeZ = input("[*] Výška zvednutí Z na konci programu [40]: ") or "40"

hlavicka = """; Generováno v routexc2gcode.py

; Vyber nástroj
T"""+str(nastroj_c)+"""M6
; Spusť vřeteno
S"""+str(otacky)+"""M3
; Zvednutí Z po startu
G00 Z5
"""

paticka = """
; zastav vřeteno
M5
; vyjetí vřetene a konec frézovaní
G00 Z"""+str(safeZ)+"""
; konec programu
M2
"""

start = input("\nPokračovat [y/n]: ")

if start != "y": sys.exit(1)

#
# Hlavni kod
#

# urceni vystupniho souboru

out = open(f"{cela_cesta_vystupu}", "w")
out.write("; "+f"{today}\n")

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

print("Hotovo.")

sys.exit(0)

