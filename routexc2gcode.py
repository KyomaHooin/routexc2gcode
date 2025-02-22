#!/usr/bin/python3
#
# Převodník routovacího Excellonu do G-code (běžných frézek)
#
#   autor: Vladimír Černý, KyomaHooin
#   email: cernyv.pdp7@gmail.com
# licence: GPLv3
#

import sys,os,re
from datetime import datetime

#
# Proměnné
#

VERSION='1.3'
RUN=None

#
# Inicializace
#

print("\nroutexc2gcode " + VERSION + "\n")

INPUT_DIR = input("[*] Název zdrojového adresáře [D:/cnc]: ") or "D:/cnc"
INPUT_FILE = input("[*] Název zdrojového souboru: ")

OUTPUT_DIR = input("[*] Název výstupního adresáře [D:/cnc/gcode]: ") or "D:/cnc/gcode"
OUTPUT_FILE = input("[*] Název výstupního souboru [test.gcode]: ") or "test.gcode"

print("\n")

otacky = input("[*] Otáčky vřetene [20000]: ") or "20000"
feedrate = input("[*] Feedrate [F300]: ") or "F300"
moveZ = input("[*] Výška přejezdu nad DPS [5]: ") or "5"
milldepth = input("[*] Hloubka frézování [-2]: ") or "-2"
nastroj_c = input("[*] Číslo nástroje [1]: ") or "1"
safeZ = input("[*] Výška zvednutí Z na konci programu [40]: ") or "40"

# Hlavička
HEADER = """; Generováno v routexc2gcode.py

; Vyber nástroj
T""" + nastroj_c + """M6
; Spusť vřeteno
S""" + otacky + """M3
; Zvednutí Z po startu
G00 Z5
"""
# Patička
FOOTER = """
; zastav vřeteno
M5
; vyjetí vřetene a konec frézovaní
G00 Z""" + safeZ + """
; konec programu
M2
"""

#
# Hlavní kód

# pohyb vřetene
# moveZ ekvivaletní k M16 v Excellonu
# M15 se vyjádří, G00 následuje G01 se stejnou souřadnicí a pohybem Z dolu (obvykle)

# Poslední souřadnice G01
XY='XY'

# test běhu
while RUN not in ('y','n'): RUN = input("\nPokračovat [y/n]: ")
if RUN == "n": sys.exit(1)

# určení výstupního souboru
try:
  out = open(os.path.join(OUTPUT_DIR, OUTPUT_FILE), "w")
except:
  print("\nNelze otevřít výstupní soubor.")   
  sys.exit(1)

# zápis hlavičky
out.write("; " + datetime.now().strftime('%m/%d/%Y %H:%M:%S') + "\n")
out.write(HEADER)

# konverze
try:
  with open(os.path.join(INPUT_DIR, INPUT_FILE), "r") as f:
    for line in f:
      #
      # G00 
      #
      if line.startswith("G00"):
        if line.strip() == 'G00XY':
          out.write("G01" + re.sub('^(.*)\s+?Z.*$','\\1', XY)) # odstraní Z souřadnici
        else:
          out.write(line)
          out.write("G01" + line.strip()[3:] + "Z" + milldepth+feedrate + "\n")
      #
      # G01
      #
      if line.startswith("G01"):
        XY = line[3:]
        out.write(XY)
      #
      # X* Y*
      #
      if line.startswith(("X","Y")):
        out.write(line)
      #
      # M15
      #
      #if line.startswith("M15"):
      #  print(milldepth, "; Vreteno dolu")
      #  milldepth = "Z-2"
      #
      # M16
      #
      if line.startswith("M16"):
        out.write("Z" + moveZ + " " + "; Vreteno nahoru\n")
      #
      # G40
      #
      #if line.startswith("G40"):
      #  print(line.strip())
      #
      # M30
      #
      if line.startswith("M30"):
        break
  f.close()
except:
  print("Nelze načíst vstupní soubor.")

# zápis patičky
out.write(FOOTER)

# uzavření výstupu
out.close()

print("Hotovo.")

sys.exit(0)

