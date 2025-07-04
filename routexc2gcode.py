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

VERSION = '1.7'

CONV_RUN = None
RUN = None

#
# Třída
#

class Coord:
  def __init__(self):
    self.X = None
    self.Y = None
    self.A = None
  def update(self, ln):
    for c in re.findall('[XYA]-?\\d*\\.?\\d+', ln):
      setattr(self, c[0], c[1:])# písmeno a numerická část

NEXT = Coord()# aktuální souřadnice
LAST = Coord()# poslední souřadnice

#
# Funkce
#

def convert(coord,unit,zero,decimal,pos,dec):
  if decimal == 'y': return coord.group(0)# řádek bez změny

  ret = coord.group(1) if coord.group(1) else '' # prefix nebo prázdno

  for c in re.findall('[XYA]-?\\d*\\.?\\d+', coord.group(2)):# všechna písmena postupně
    val = c[1:]# numerická část

    if zero == 't':# trailing zero
      val = val[:-dec] + '.' + val[-dec:]
    if zero == 'l':# leading zero
      if '-' in val: pos = pos + 1
      val = val.zfill(pos)# LZ fix
      val = val[:pos] + '.' + val[pos:]

    ret = ret + c[0] + str(round(float(val) * unit, 4))# převedené písmeno a numerická část

  return ret + coord.group(3) # suffix

def arc(x1,y1,x2,y2,r,pref):

  Sx = (float(x1) + float(x2)) / 2 # střed úsečky v X
  Sy = (float(y1) + float(y2)) / 2 # střed úsečky v Y
 
  rozdilX = float(x2) - float(x1) # rozdíl mezi body oblouku v X
  rozdilY = float(y2) - float(y1) # rozdíl mezi body oblouku v Y
 
  # délka poloviční tětivy (střed úsečky mezi koncovými body oblouku, bod "S")
  d = math.sqrt(math.pow(-rozdilX, 2) + rozdilY**2) / 2
 
  # vzdálenost středu oblouku od toho "S" (Pytaghorova věta)
  h = math.sqrt(float(r)**2 - d**2)

  # normalizovaný (jednotkový) normálový vektor
  mikroNX = rozdilY / math.sqrt(math.pow(-rozdilX, 2) + rozdilY**2) # osa X
  mikroNY = rozdilX / math.sqrt(math.pow(-rozdilX, 2) + rozdilY**2) # osa Y

  # výpočet X,Y souřadnic středu oblouku
  if pref == 'G02':
    centerX = Sx + h * mikroNX
    centerY = Sy - h * mikroNY
  if pref == 'G03':
    centerX = Sx - h * mikroNX
    centerY = Sy + h * mikroNY

  # výpočet I, J
  I = round(centerX - float(x1), 4)
  J = round(centerY - float(y1), 4)

  return 'I' + str(I) + 'J' + str(J)

#
# Inicializace
#

print("\nroutexc2gcode " + VERSION + "\n")

INPUT_DIR = input('[*] Název zdrojového adresáře [D:/cnc]: ') or 'D:/cnc'
INPUT_FILE = input('[*] Název zdrojového souboru: ')

OUTPUT_DIR = input('[*] Název výstupního adresáře [D:/cnc/gcode]: ') or 'D:/cnc/gcode'
OUTPUT_FILE = input('[*] Název výstupního souboru [test.gcode]: ') or 'test.gcode'

print()

otacky = input('[*] Otáčky vřetene [17500]: ') or '17500'
feedrate = input('[*] Feedrate [F300]: ') or 'F300'
moveZ = input('[*] Výška přejezdu nad DPS [5]: ') or '5'
milldepth = input('[*] Hloubka frézování [-2]: ') or '-2'
nastroj_c = input('[*] Číslo nástroje [1]: ') or '1'
safeZ = input('[*] Výška zvednutí Z na konci programu [40]: ') or '40'
chlazeni = input ('[*] Chlazení vřetene y/n? [n]: ') or ''

# Chlazení
if chlazeni == 'y': chlazeni = 'M8'

print()
print('Fromát souřadnic:')
print()

# Jednotky INCH/METRIC
unit = None
while unit not in ('mm','inch'): unit = input('[*] Jednotky [mm/inch]: ')
unit = 1 if unit == 'mm' else 25.4
# Decimal
decimal = None
while decimal not in ('y','n'): decimal = input ('[*] Desetinná značka? [y/n]: ')
# LZ/TZ; pos/dec
zero,pos,dec = None,None,None
if decimal == 'n':
  while zero not in ('l','t'): zero = input('[*] Vedoucí, nebo koncové nuly? [l/t]: ')
  pos = int(input('[*] Počet celých číslic? [3]: ') or 3)
  dec = int(input('[*] Počet desetinných číslic? [3]: ') or 3)

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
G00 Z""" + moveZ + """
"""

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
# KONVERZE SOUŘADNIC
#

while CONV_RUN not in ('y','n'): CONV_RUN = input('Provést konverzi souřadnic? [y/n]: ')
if CONV_RUN == 'y':

  # určení výstupního souboru konverze souřadnic
  try:
    out = open(os.path.join(INPUT_DIR, INPUT_FILE + '.conv'), 'w')
  except:
    print('Nelze otevřít výstupní soubor koverze.')
    sys.exit(1)

  # konverze souřadnic
  try:
    with open(os.path.join(INPUT_DIR, INPUT_FILE), 'r') as f:
      for line in f:
        match = re.match('^(G..)?((?:[XYA]-?\\d*\\.?\\d+)+)(.*)$', line)# prefix + všechna písmena + suffix
        if match:
          out.write(convert(match,unit,zero,decimal,pos,dec) + "\n")
        else:
          out.write(line)
  except:
    print('Nelze načíst vstupní soubor konverze.')

  # uzavření výstupu
  out.close()
  print('Hotovo.')
  print()

#
# PŘEVOD G-CODE
#

while RUN not in ('y','n'): RUN = input('Pokračovat [y/n]: ')
if RUN == 'n': sys.exit(1)

# určení výstupního souboru
try:
  out = open(os.path.join(OUTPUT_DIR, OUTPUT_FILE), 'w')
except:
  print('Nelze otevřít výstupní soubor.')
  sys.exit(1)

# zápis hlavičky
out.write('; ' + datetime.now().strftime('%m/%d/%Y %H:%M:%S') + "\n")
out.write(HEADER)

# nastavení vstupního souboru
if CONV_RUN == 'y': INPUT_FILE = INPUT_FILE + '.conv'

# konverze
try:
  with open(os.path.join(INPUT_DIR, INPUT_FILE), 'r') as f:
    for line in f:
      # uložení aktuální souřadnice
      NEXT.update(line)
      #
      # G00 
      #
      if line.startswith('G00'):
        if line.strip() == 'G00XY': # ošetření výrazu G00XY generovaného FAB3000
          out.write('G00' + 'X' + LAST.X + 'Y' + LAST.Y + "\n")
          out.write('G01' + 'X' + LAST.X + 'Y' + LAST.Y + 'Z' + milldepth + feedrate + "\n")
        else:
          out.write(line)
          out.write('G01' + 'X' + NEXT.X + 'Y' + NEXT.Y + 'Z' + milldepth + feedrate + "\n")
      #
      # G01
      #
      if line.startswith('G01'):
        out.write(line.strip() + 'Z' + milldepth + feedrate + "\n")
      #
      # G02
      #
      if line.startswith('G02'):
        out.write('G02' + 'X' + NEXT.X + 'Y' + NEXT.Y + arc(LAST.X,LAST.Y,NEXT.X,NEXT.Y,NEXT.A,'G02') + feedrate + "\n")
      #
      # G03
      #
      if line.startswith('G03'):
        out.write('G03' + 'X' + NEXT.X + 'Y' + NEXT.Y + arc(LAST.X,LAST.Y,NEXT.X,NEXT.Y,NEXT.A,'G03') + feedrate + "\n")
      #
      # X* Y*
      #
      if line.startswith(('X','Y')):
        out.write(line)
      #
      # M16
      #
      if line.startswith('M16'):
        out.write('Z' + moveZ + ' ; Vřeteno nahoru' + "\n")
      #
      # M30
      #
      if line.startswith('M30'):
        break
      # uložení poslední souřadnice
      LAST.update(line)
except:
  print('Nelze načíst vstupní soubor.')

# zápis patičky
out.write(FOOTER)

# uzavření výstupu
out.close()
print('Hotovo.')

sys.exit(0)

