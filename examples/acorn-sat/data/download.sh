#/bin/bash
echo "Begining data acquisition..."
curl http://www.bom.gov.au/climate/change/acorn-sat/map/stations-acorn-sat.txt | tail -n +2 | grep -v "^$" | cut -d',' -f1 | sed -e 's/^ *//' -e 's/ *$//' > station_list.txt

while read station; do
    echo Downloading data for `printf %03d ${station}`...
    curl -O http://www.bom.gov.au/climate/change/acorn/sat/data/acorn.sat.minT.`printf %06d ${station}`.daily.txt
    curl -O http://www.bom.gov.au/climate/change/acorn/sat/data/acorn.sat.maxT.`printf %06d ${station}`.daily.txt
done < station_list.txt
