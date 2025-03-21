#!/usr/bin/python3
#
# Převodník routovacího Excellonu do G-code (běžných frézek)
#
#   autor: Vladimír Černý, KyomaHooin
#   email: cernyv.pdp7@gmail.com
# licence: GPLv3
#

import math,sys,os,re
from datetime import datetime

#
# Proměnné
#

VERSION='1.5'
RUN=None

#
# Funkce
#

def oblouk(x1,y1,x2,y2,r):
  # střed úsečky v X
  Sx = (x1 + x2) / 2
 
  # střed úsečky v Y
  Sy = (y1 + y2) / 2
 
  # rozdíl mezi body oblouku v X
  rozdilX = x1 - x2
 
  # rozdíl mezi body oblouku v Y
  rozdilY = y1 - y2
 
  # délka poloviční tětivy (střed úsečky mezi koncovými body oblouku, bod "S")
  d = math.sqrt(math.pow(-rozdilX, 2) + rozdilY**2) / 2
 
  # vzdálenost středu oblouku od toho "S" (Pytaghorova věta)
  h = math.sqrt(r**2 - d**2)

  # normalizovaný (jednotkový) normálový vektor
  mikroNX = rozdilY / math.sqrt(math.pow(-rozdilX, 2) + rozdilY**2) # osa X
  mikroNY = rozdilX / math.sqrt(math.pow(-rozdilX, 2) + rozdilY**2) # osa Y

  # výpočet X,Y souřadnic středu oblouku
  centerX = round(Sx + h * mikroNX, 4)
  centerY = round(Sy - h * mikroNY, 4)
  # výpočet I, J
  I = centerX - x1
  J = y1 - centerY

  return "X" + str(x2) + "Y" + str(y2) + "I" + str(I) + "J" + str(J)

#
# Inicializace
#

print("\nroutexc2gcode " + VERSION + "\n")

INPUT_DIR = input("[*] Název zdrojového adresáře [D:/cnc]: ") or "D:/cnc"
INPUT_FILE = input("[*] Název zdrojového souboru: ")

OUTPUT_DIR = input("[*] Název výstupního adresáře [D:/cnc/gcode]: ") or "D:/cnc/gcode"
OUTPUT_FILE = input("[*] Název výstupního souboru [test.gcode]: ") or "test.gcode"

print()

otacky = input("[*] Otáčky vřetene [20000]: ") or "20000"
feedrate = input("[*] Feedrate [F300]: ") or "F300"
moveZ = input("[*] Výška přejezdu nad DPS [5]: ") or "5"
milldepth = input("[*] Hloubka frézování [-2]: ") or "-2"
nastroj_c = input("[*] Číslo nástroje [1]: ") or "1"
safeZ = input("[*] Výška zvednutí Z na konci programu [40]: ") or "40"
chlazeni = input ("[*] Chlazení vřetene y/n? [n]: ") or ""

# Chlazení
if chlazeni == "y": chlazeni = "M8"

print()

# Hlavička
HEADER = """; Generováno v routexc2gcode.py

; Vyber nástroj
T""" + nastroj_c + """M6
; Chlazení
""" + chlazeni + """
; Spusť vřeteno
S""" + otacky + """M3
; Zvednutí Z po startu
G00 Z5"""

# Patička
FOOTER = """
; Chlazení
""" + chlazeni.replace('8','9') + """
; zastav vřeteno
M5
; vyjetí vřetene a konec frézovaní
G00 Z""" + safeZ + """
; konec programu
M2"""

#
# Hlavní kód
#
# pohyb vřetene
# moveZ ekvivaletní k M16 v Excellonu
# M15 se vyjádří, G00 následuje G01 se stejnou souřadnicí a pohybem Z dolu (obvykle)

# Poslední souřadnice G01
LAST_G01='XY'

# test běhu
while RUN not in ('y','n'): RUN = input("Pokračovat [y/n]: ")
if RUN == "n": sys.exit(1)

# určení výstupního souboru
try:
  out = open(os.path.join(OUTPUT_DIR, OUTPUT_FILE), "w")
except:
  print("Nelze otevřít výstupní soubor.")   
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
        if line.strip() == 'G00XY': # ošetření výrazu G00XY generovaného FAB3000
          out.write("G00" + re.sub('^(.*)\\s+?Z.*$','\\1', LAST_G01)) # odstraní Z souřadnici          
          out.write("G01" + re.sub('^(.*)\\s+?Z.*$','\\1', LAST_G01).strip() + "Z" + milldepth + feedrate + "\n")
        else:
          out.write(line)
          out.write("G01" + line.strip()[3:] + "Z" + milldepth + feedrate + "\n")
      #
      # G01
      #
      if line.startswith("G01"):
        LAST_G01 = line[3:]
        out.write(XY)
      #
      # G02
      #
      if line.startswith("G02"):
        LAST_G02 = line[3:] # ulozeni hodnoty pro G03
        prefix = line[:3]
        x1 = float(re.sub('^X(.*)Y.*$','\\1', LAST_G01))
        y1 = float(re.sub('^.*Y(.*)$','\\1', LAST_G01).split('Z')[0].strip())
        x2 = float(re.sub('^X(.*)Y.*$','\\1', line[3:]))
        y2 = float(re.sub('^.*Y(.*)$','\\1', line[3:]).split('A')[0].strip())
        r = float(re.sub('^.*A(.*)$','\\1', line[3:]).strip())
        out.write(prefix + oblouk(x1, y1, x2, y2, r))
      #
      # G03
      #
      if line.startswith("G03"):
         prefix = line[:3]
         x1 = float(re.sub('^X(.*)Y.*$','\\1', LAST_G02))
         y1 = float(re.sub('^.*Y(.*)$','\\1', LAST_G02).split('A')[0].strip())
         x2 = float(re.sub('^X(.*)Y.*$','\\1', line[3:]))
         y2 = float(re.sub('^.*Y(.*)$','\\1', line[3:]).split('A')[0].strip())
         r = float(re.sub('^.*A(.*)$','\\1', line[3:]).strip())
         out.write(prefix + oblouk(x1, y1, x2, y2, r))
      #
      # X* Y*
      #
      if line.startswith(("X","Y")):
        out.write(line)
      #
      # M15
      #
      #if line.startswith("M15"):
      #  print(milldepth, "; Vřeteno dolu")
      #  milldepth = "Z-2"
      #
      # M16
      #
      if line.startswith("M16"):
        out.write("Z" + moveZ + " " + "; Vřeteno nahoru\n")
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
except:
  print("Nelze načíst vstupní soubor.")

# zápis patičky
out.write(FOOTER)

# uzavření výstupu
out.close()

print("Hotovo.")

sys.exit(0)

