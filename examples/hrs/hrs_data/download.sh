# For a list of station IDs get the site_config.json from bom.gov.au
curl http://www.bom.gov.au/water/hrs/content/config/site_config.json > site_config.json

# Download each daily timeseries CSV file from bom.gov.au
for station in `python list_hrs.py`; do wget "http://www.bom.gov.au/water/hrs/content/data/$station/${station}_daily_ts.csv"; done;

