del armybuilder.zip
cd src
python setup_ab.py py2exe
cd ..
move src\dist\* src\
rmdir src\dist
del /Q src\build\*
rmdir /S /Q src\build
"C:\Program Files\7-Zip\7z.exe" a armybuilder.zip "src" "data\kow" "data\icons" "data\*.csv" "armybuilder.bat"