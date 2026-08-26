@echo off
rem Start de stamboomwebsite, ook bereikbaar voor andere apparaten
rem op hetzelfde (wifi)netwerk. Het adres staat in het venster.
cd /d "%~dp0"
py server.py --netwerk
pause
