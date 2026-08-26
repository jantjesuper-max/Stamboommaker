#!/bin/sh
# Start de stamboomwebsite, ook bereikbaar voor andere apparaten op hetzelfde
# (wifi)netwerk. Het adres staat in het venster.
cd "$(dirname "$0")" || exit 1
python3 server.py --netwerk
