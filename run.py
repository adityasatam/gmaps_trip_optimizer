import requests
import numpy as np

# 1) copy this run.py in your local VS Code.
# 2) only modify gmap_url parameter (line 15) with gmap url links (multiple links incase of more than 10 locations).
# 3) execute run.py in your local VS Code.

url = "https://raw.githubusercontent.com/adityasatam/gmaps_trip_optimizer/refs/heads/main/main.py"
response = requests.get(url)

if response.status_code == 200:
    exec(response.text)
    #print(response.text)
    main(gmap_url=["https://www.google.com/maps/dir/Ramky+One+Kosmos,+Eco+Art+Studio,+Ramky+One+Kosmos+Rd,+Tellapur,+Hyderabad,+Nallagandla,+Telangana+500046/Shah+Ghouse+Hotel+%26+Restaurant,+Gachibowli,+Villa-8,+Gachibowli+Rd,+opposite+Bio+Diversity+Park,+Raidurgam,+Madhura+Nagar+Colony,+Gachibowli,+Hyderabad,+Telangana+500104/Golconda+Fort,+Hyderabad,+Telangana/Micron+Technology+Aquila,+Phoenix+-+Aquila+Block+A+Financial+District,+Nankaramguda,+Serilingampalle+(M),+Hyderabad,+Telangana+500032/@17.4187615,78.313202,13z/data=!3m1!4b1!4m26!4m25!1m5!1m1!1s0x3bcb9327b3c2efe1:0xfd50a105df6e72e!2m2!1d78.3045696!2d17.4617084!1m5!1m1!1s0x3bcb93f96a9c5151:0xc3acabf7b492dc17!2m2!1d78.3762853!2d17.4267841!1m5!1m1!1s0x3bcb968c5f1342f3:0xd752a9bdbdde84df!2m2!1d78.4033392!2d17.3847636!1m5!1m1!1s0x3bcb95b81f90ab95:0xd3005ecbfbd05f8b!2m2!1d78.340366!2d17.4173728!3e9?entry=ttu&g_ep=EgoyMDI2MDMwNC4xIKXMDSoASAFQAw%3D%3D"
      , "https://www.google.com/maps/dir/Shubam+Royal+Apartments,+Friends+Colony,+Puppal+Guda,+Qutub+Shahi+Tombs,+Hyderabad,+Manikonda,+Telangana+500089,+India/Manikonda+Sub+Post+Office,+C92G%2BVVX,+Manikonda+Garden,+Sri+Balaji+Nagar+Colony,+Hyderabad,+Telangana+500089/Babai+Hotel+Manikonda,+G7,+G8,+C92Q%2BCHM,+Old+Tharuni+Super+Market,+Aashritha+Meadows,+Shaikpet+Main+Rd,+beside+SBI,+Dream+Valley,+Tanasha+Nagar,+Puppalguda,+Hyderabad,+Manikonda,+Telangana+500089/Mehfil+Restaurant,+Whisper+Valley+Road,+Narne+Road,+opp.+JRC+Conventional+Center,+Shaikpet,+Hyderabad,+Telangana+500104/@17.4084592,78.3758072,15z/data=!3m1!4b1!4m25!4m24!1m5!1m1!1s0x3bcb96a2120955f1:0xf5c3c4f4b0c80b07!2m2!1d78.39105!2d17.3999503!1m5!1m1!1s0x3bcb94193d6d70eb:0x3466d46b83cdf94b!2m2!1d78.3772435!2d17.4022336!1m5!1m1!1s0x3bcb977cfa74a4ed:0x977c30fccd1c8b89!2m2!1d78.3883722!2d17.4005477!1m5!1m1!1s0x3bcb96ae37b2744b:0x27a0b4efcb901e4a!2m2!1d78.3942405!2d17.4144473?entry=ttu&g_ep=EgoyMDI2MDMwNC4xIKXMDSoASAFQAw%3D%3D"]
      , optimize_by=['time', 'dist'])
else:
    print("Failed to execute the github code")
