# gmaps_trip_optimizer  
Finds the optimal route for multiple destinations using live Google Maps travel data and an exact TSP solver.  
  
# 🚀 Problem This Solves  
When planning trips with multiple destinations, Google Maps cannot optimize complex routes and limits routes to about 10 waypoints. This code calculates the optimal route algorithmically and removes the 10 waypoint limitation.   
  
# ⚙️How It Works  
Reads destinations from a Google Maps route URLs, then fetches live Google Maps travel data.
Builds an asymmetric distance/time matrix and solves the Traveling Salesman Problem (TSP) to compute the optimal route.
Outputs the optimized round trip and creates a Google Maps navigation link.  
  
# 📥 Input  
# Google Maps Route URL  
Search multiple destinations route in Google Maps, and copy the gmap URL into the gmap_url parameter (run.py).  
  
# 🐦 Main  
main(gmap_url = ["https://www.google.com/maps/dir/Place1/Place2/Place3/Place4/Place5/Place6/Place7/Place8/Place9/Place10"
    , "https://www.google.com/maps/dir/Place11/Place12/Place13/Place14"]
    , optimize_by = ['time', 'dist'])  
  
# Parameters:
1. gmap_url (list[str]) - Google Maps route URL containing all destinations.  
2. optimize_by (list[str]) – Optimization criteria for route calculation.  
"time" → Finds route with minimum travel time  
"dist" → Finds route with minimum travel distance
