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
    main(gmap_url="https://www.google.com/maps/dir/Ramky+One+Kosmos,+Eco+Art+Studio,+Ramky+One+Kosmos+Rd,+Tellapur,+Hyderabad,+Nallagandla,+Telangana+500046/Shah+Ghouse+Hotel+%26+Restaurant,+Gachibowli,+Villa-8,+Gachibowli+Rd,+opposite+Bio+Diversity+Park,+Raidurgam,+Madhura+Nagar+Colony,+Gachibowli,+Hyderabad,+Telangana+500104/Golconda+Fort,+Hyderabad,+Telangana/Micron+Technology+Aquila,+Phoenix+-+Aquila+Block+A+Financial+District,+Nankaramguda,+Serilingampalle+(M),+Hyderabad,+Telangana+500032/@17.4187615,78.313202,13z/data=!3m1!4b1!4m26!4m25!1m5!1m1!1s0x3bcb9327b3c2efe1:0xfd50a105df6e72e!2m2!1d78.3045696!2d17.4617084!1m5!1m1!1s0x3bcb93f96a9c5151:0xc3acabf7b492dc17!2m2!1d78.3762853!2d17.4267841!1m5!1m1!1s0x3bcb968c5f1342f3:0xd752a9bdbdde84df!2m2!1d78.4033392!2d17.3847636!1m5!1m1!1s0x3bcb95b81f90ab95:0xd3005ecbfbd05f8b!2m2!1d78.340366!2d17.4173728!3e9?entry=ttu&g_ep=EgoyMDI2MDMwNC4xIKXMDSoASAFQAw%3D%3D"
      , full_file_path=r"C:/Users/sasuk/travelling_salesman/sample_destinations.txt"
      , parameters=['time', 'dist'])
else:
    print("Failed to execute the github code")
