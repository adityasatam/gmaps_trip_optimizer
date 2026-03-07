# gmaps_trip_optimizer  
Finds the optimal route for multiple destinations using live Google Maps travel data and an exact TSP solver.  
  
# 🚀 Problem This Solves  
When planning trips with multiple destinations, Google Maps cannot optimize complex routes and limits routes to about 10 waypoints. This code calculates the optimal route algorithmically and removes the 10 waypoint limitation.   
  
# ⚙️How It Works  
Reads destinations from a Google Maps route URL or a local text file, then fetches live Google Maps travel data.
Builds an asymmetric distance/time matrix and solves the Traveling Salesman Problem (TSP) to compute the optimal route.
Outputs the optimized round trip and creates a Google Maps navigation link.  
  
# 📥 Input  
# Option 1 — Destination File  
Save destinations in a local input file: sample_destinations.txt  
  
Source Location  
Destination 1  
Destination 2  
Destination 3  
...  
  
The first line is the starting point, and the trip returns to it.  
Each destination must be on a separate line.  
Copy the destination name from the Google Maps search box into the destination text file.
  
# Option 2 — Google Maps Route URL  
Search multiple destinations route in Google Maps, and copy the gmap URL into the gmap_url parameter (run.py).  
  
# 🐦 Main  
main(gmap_url = "https://www.google.com/maps/dir/Place1/Place2/Place3/Place4"  
    , full_file_path = "C:/Users/sample_destinations.txt"  
    , parameters = ['time', 'dist'])  
  
# Parameters:
1. gmap_url (str) - Google Maps route URL containing all destinations.  
2. full_file_path (str) – Full path to the destination input file. Ex: "C:/Users/sample_destinations.txt"  
3. parameters (list[str]) – Optimization criteria for route calculation.  
"time" → Finds route with minimum travel time  
"dist" → Finds route with minimum travel distance
