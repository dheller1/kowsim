# -*- coding: utf-8 -*-

# util/csv_util.py
#===============================================================================
import codecs, csv

def ReadLinesFromCsv(filename, codepage='utf-8'):
   csvLines = []
   with codecs.open(filename, 'r', codepage) as f:
      csvReader = unicode_csv_reader(f, delimiter=',')
      csvLines = [line for line in csvReader]
      
   return csvLines
 
def utf_8_encoder(unicode_csv_data):
   for line in unicode_csv_data:
      yield line.encode('utf-8')

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
   # csv.py doesn't do Unicode; encode temporarily as UTF-8:
   csv_reader = csv.reader(utf_8_encoder(unicode_csv_data), dialect=dialect, **kwargs)
   for row in csv_reader:
      # decode UTF-8 back to Unicode, cell by cell:
      yield [unicode(cell, 'utf-8') for cell in row]

#===============================================================================
# CsvParser
#   Abstract base class for a CSV Parser object. Subclasses should reimplement
#   Parse() which returns an object read from a CSV file.
#
#   Usage of a CsvParser object:
#    1) Call ReadLinesFromFile()
#    2) Call Parse() to generate an object from the input data
#===============================================================================
class CsvParser(object):
   def __init__(self):
      self._csvLines = []
      
   def Parse(self):
      raise TypeError("Abstract base class CsvParser instantiated.")
      return None

   def ReadLinesFromFile(self, filename, codepage='utf-8'):
      self._csvLines = []
      with codecs.open(filename, 'r', codepage) as f:
         csvReader = unicode_csv_reader(f, delimiter=',')
         self._csvLines = [line for line in csvReader]
         