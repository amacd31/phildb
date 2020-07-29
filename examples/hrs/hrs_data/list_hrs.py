import json

x = json.load(open("site_config.json"))

for station in x["stations"]["features"]:
    print(station["properties"]["AWRC_ID"])
