import math, csv 

def dot2d(vec1, vec2):
    return vec1.x() * vec2.x() + vec1.y() * vec2.y()
 
def len2d(vec):
    return math.sqrt( vec.x()*vec.x() + vec.y()*vec.y() )
 
def dist2d(p1, p2):
   dx = p1.x() - p2.x()
   dy = p1.y() - p2.y()
   return math.sqrt( dx**2 + dy**2 )
 
def utf_8_encoder(unicode_csv_data):
   for line in unicode_csv_data:
      yield line.encode('utf-8')

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
   # csv.py doesn't do Unicode; encode temporarily as UTF-8:
   csv_reader = csv.reader(utf_8_encoder(unicode_csv_data), dialect=dialect, **kwargs)
   for row in csv_reader:
      # decode UTF-8 back to Unicode, cell by cell:
      yield [unicode(cell, 'utf-8') for cell in row]