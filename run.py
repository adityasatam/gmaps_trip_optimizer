import requests
import numpy as np

# 1) keep your destinations file in .txt format in local folder.
# 2) copy this run.py in your local VS Code.
# 4) modify only line 15 with full file path of the txt file with all destinations.
# 5) execute run.py in your local VS Code.

url = "https://raw.githubusercontent.com/adityasatam/gmaps_trip_optimizer/refs/heads/main/main.py"
response = requests.get(url)

if response.status_code == 200:
    exec(response.text)
    #print(response.text)
    main(places_fullfilepath='C:/Users/sasuk/travelling_salesman/destinations.txt')
else:
    print("Failed to execute the github code")
