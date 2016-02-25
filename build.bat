python src\setup.py py2exe
rm kowsim.zip
"C:\Program Files\7-Zip\7z.exe" a kowsim.zip "dist" "data" "kowsim.bat"