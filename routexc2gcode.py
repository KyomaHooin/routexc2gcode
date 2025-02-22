#!/usr/bin/python3
#
# Převodník routovacího Excellonu do G-code (běžných frézek)
#
#   autor: Vladimír Černý
#   email: cernyv.pdp7@gmail.com
# licence: GPLv3
#

import sys,os,re
from datetime import datetime

#
# Proměnné
#

VERSION='1.2'
RUN=None

#
# Inicializace
#

print("\nroutexc2gcode " + VERSION + "\n")

zdrojovy_adresar = input("[*] Název zdrojového adresáře [D:/cnc/]: ") or "D:/cnc/"
zdrojovy_soubor = input("[*] Název zdrojového souboru: ")

cela_cesta_vstupu = os.path.join(zdrojovy_adresar, zdrojovy_soubor)

vystupni_adresar = input("[*] Název výstupního adresáře [D:/cnc/gcode/]: ") or "D:/cnc/gcode/"
vystupni_soubor  = input("[*] Název výstupního souboru [test.gcode]: ") or "test.gcode"

cela_cesta_vystupu = os.path.join(vystupni_adresar, vystupni_soubor)

otacky = input("\n[*] Otáčky vřetene [20000]: ") or "20000"
feedrate = input("[*] Feedrate [F300]: ") or "F300"
moveZ = input("[*] Výška přejezdu nad DPS [5]: ") or "5"
milldepth = input("[*] Hloubka frézování [-2]: ") or "-2"
nastroj_c = input("[*] Číslo nástroje [1]: ") or "1"
safeZ = input("[*] Výška zvednutí Z na konci programu [40]: ") or "40"

hlavicka = """; Generováno v routexc2gcode.py

; Vyber nástroj
T""" + nastroj_c + """M6
; Spusť vřeteno
S""" + otacky + """M3
; Zvednutí Z po startu
G00 Z5
"""

paticka = """
; zastav vřeteno
M5
; vyjetí vřetene a konec frézovaní
G00 Z""" + safeZ + """
; konec programu
M2
"""

#
# Hlavní kód
#

while RUN not in ('y','n'): RUN = input("\nPokračovat [y/n]: ")
if RUN == "n": sys.exit(1)

# určení výstupního souboru
out = open(cela_cesta_vystupu, "w")
out.write("; " + datetime.now().strftime('%m/%d/%Y %H:%M:%S') + "\n")

# zápis hlavičky
out.write(hlavicka)

# pohyb vřetene
# moveZ ekvivaletní k M16 v Excellonu
# M15 se vyjádří, G00 následuje G01 se stejnou souřadnicí a pohybem Z dolu (obvykle)

# Poslední souřadnice G01
XY='XY'

with open(cela_cesta_vstupu, "r") as f:
  line = f.readline()
  while line:
    line = f.readline()
    if line.startswith("G00"):
      if line.strip() == 'G00XY':
        out.write("G01" + re.sub('^(.*)\s+?Z.*$','\\1', XY)) # odstraní Z souřadnici
      else:
        out.write(line)
        out.write("G01" + line.strip()[3:] + "Z" + milldepth+feedrate + "\n")
    if line.startswith("G01"):
      XY = line[3:]
      out.write(XY)
    if line.startswith(("X","Y")):
      out.write(line)
    #if line.startswith("M15"):
      #print(milldepth, "; Vreteno dolu")
      #milldepth = "Z-2"
    if line.startswith("M16"):
      out.write("Z" + moveZ + " " + "; Vreteno nahoru\n")
    #if line.startswith("G40"):
    #  print(line.strip())
    if line.startswith("M30"):
      break
f.close()

# zápis patičky
out.write(paticka)

# uzavření výstupu
out.close()

print("Hotovo.")

sys.exit(0)

