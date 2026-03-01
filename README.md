# gmaps_trip_optimizer
Optimizes multi-destination trips using live Google Maps distance data and a Traveling Salesman (TSP) algorithm, supporting asymmetric routes and unlimited locations.  

# 🚀 Problem This Solves
When planning a multi-destination trip. Google Maps does not always optimize complex routes automatically.  
Traffic-based travel time varies depending on departure time. Distance from A → B may differ from B → A.  
Google Maps restricts waypoint count (max 10 locations). It overcomes this limitation using algorithmic optimization.  

# ⚙️How It Works  
Reads destinations from a text file and Fetches live Google Maps distance & travel stats  
Builds an asymmetric distance matrix & Solves the Traveling Salesman Problem (TSP)  
Prints an optimized round trip. Opens the final optimized route in Google Maps (within waypoint limits)  

# 📥 Input  
Save a local input sample_destinations.txt file containing destinations:  
  
Source Location  
Destination 1  
Destination 2  
Destination 3  
...  
  
The first line is treated as the starting point & each destination must be on a new line.  
The trip will always return to this source location.  
Search destination name in gmap and copy it from destination box into local destination txt file.
