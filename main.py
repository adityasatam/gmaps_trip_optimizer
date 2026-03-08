from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from functools import lru_cache
import re
from itertools import islice
from urllib.parse import urlparse


def create_places_dict(gmap_url):
    places = []

    for url in gmap_url:
        
        route_part = url.split("/dir/")[1].split("/@")[0]
        
        # split locations
        places.extend(route_part.split("/"))

        # remove duplicates while keeping order
        places = list(dict.fromkeys(places))

        # build dictionary
        places_dict = {f"p{i}": place for i, place in enumerate(places)}
    
    return places_dict


def create_route_url_dict(places_dict):
    route_url_dict = {}
    keys = list(places_dict.keys())

    for i in range(len(keys)):
        for j in range(len(keys)):
            if i != j:
                route = f"{keys[i]}/{keys[j]}" #k1, k2
                url = f"https://www.google.com/maps/dir/{places_dict[keys[i]]}/{places_dict[keys[j]]}" #v1, v2
                route_url_dict[route] = url

    return route_url_dict


def scrape_in_batches(route_url_dict, batch_size=30):

    raw_route_time_dist_dict = {}

    keys = list(route_url_dict.keys())

    for i in range(0, len(keys), batch_size):

        batch_keys = keys[i:i+batch_size]

        batch_dict = {k: route_url_dict[k] for k in batch_keys}

        batch_result = scrape_time_dist_from_gmaps(batch_dict)

        raw_route_time_dist_dict.update(batch_result)

    return raw_route_time_dist_dict


def scrape_time_dist_from_gmaps(route_url_dict):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--force-device-scale-factor=0.9")
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    raw_route_time_dist_dict = {}

    pattern = re.compile(
            r"\d+\s*hr(?:\s*\d+\s*min)?|"
            r"\d+\s*hr(?:\s*\d+\s*m)?|"
            r"\d+\s*h(?:\s*\d+\s*m)?|"
            r"\d+\s*h(?:\s*\d+\s*min)?|"
            r"\d+\s*min|"
            r"\d+(?:\.\d+)?\s*m|"
            r"\d+(?:\.\d+)?\s*km"
        )
    
    for route_key, route_url in route_url_dict.items():
        driver.get(route_url)

        wait = WebDriverWait(driver, 10)

        xpath_expr = ("//div[contains(text(),'hr') or contains(text(),'min') or "
                    "contains(text(),'h') or contains(text(),'m') or contains(text(),'km')]")

        wait.until(EC.presence_of_element_located((By.XPATH, xpath_expr)))

        elements = driver.find_elements(By.XPATH, xpath_expr)

        extracted_values = []

        for el in elements:
            matches = pattern.findall(el.text)
            for match in matches:
                extracted_values.append(match.strip())

        raw_route_time_dist_dict[route_key] = extracted_values

    driver.quit()
    return raw_route_time_dist_dict


def classify_value(value):
    val = value.lower().strip()

    if re.search(r'\b\d+(\.\d+)?\s*km\b', val):
        return "distance"

    if re.search(r'\b\d+\s*m\b', val) and not re.search(r'h|min', val):
        return "distance"

    if re.search(r'\b\d+\s*(h|hr)\b', val):
        return "time"

    if re.search(r'\b\d+\s*(m|min)\b', val):
        return "time"

    return None


def valid_time_dist_pairs(raw_route_time_dist_dict):

    route_time_dist_dict = {}

    for route, values in raw_route_time_dist_dict.items():
        pairs = []
        i = 0

        while i < len(values) - 1:
            current = values[i]
            nxt = values[i + 1]

            if classify_value(current) == "time" and classify_value(nxt) == "distance":
                pairs.append((current.strip(), nxt.strip()))
                i += 2
            else:
                i += 1

        route_time_dist_dict[route] = pairs

    return route_time_dist_dict


def convert_time_to_mins(time_str):
    time_str = time_str.lower().strip()

    # Match hours (h or hr)
    hr_match = re.search(r'(\d+)\s*(?:h|hr)\b', time_str)

    # Match minutes (m or min)
    min_match = re.search(r'(\d+)\s*(?:m|min)\b', time_str)

    hours = int(hr_match.group(1)) if hr_match else 0
    minutes = int(min_match.group(1)) if min_match else 0

    return hours * 60 + minutes


def convert_dist_to_km(dist_str):
    dist_str = dist_str.lower().strip()

    km_match = re.search(r'(\d+(?:\.\d+)?)\s*km\b', dist_str)
    m_match = re.search(r'(\d+(?:\.\d+)?)\s*m\b', dist_str)

    if km_match:
        return float(km_match.group(1))

    if m_match:
        return float(m_match.group(1)) / 1000

    return 0


def min_route_time_dist(route_time_dist_dict, param):
    min_route_time_dist_dict = {}

    for route, pairs in route_time_dist_dict.items():

        times = []
        dists = []

        for time_str, dist_str in pairs:
            time_min = convert_time_to_mins(time_str)
            dist_m = convert_dist_to_km(dist_str)

            times.append(time_min)
            dists.append(dist_m)

        if param == "dist":
            min_route_time_dist_dict[route] = min(dists) if dists else None

        elif param == "time":
            min_route_time_dist_dict[route] = min(times) if times else None

        else:
            raise ValueError("param must be 'dist' or 'time'")

    return min_route_time_dist_dict


def create_matrix(min_route_time_dist_dict, places_dict):

    # Keep original order
    places = list(places_dict.keys())

    n = len(places)

    matrix = [[0]*n for _ in range(n)]

    index = {place: i for i, place in enumerate(places)}

    for key, value in min_route_time_dist_dict.items():
        p1, p2 = key.split('/')

        i = index[p1]
        j = index[p2]

        matrix[i][j] = value

    return matrix, places


def solve_tsp_with_path(matrix):
    n = len(matrix)

    @lru_cache(None)
    def dp(mask, pos):
        # all cities visited → return to start
        if mask == (1 << n) - 1:
            return matrix[pos][0], [0]

        min_cost = float("inf")
        best_path = []

        for city in range(n):
            if not (mask & (1 << city)):

                cost, sub_path = dp(mask | (1 << city), city)
                cost += matrix[pos][city]

                if cost < min_cost:
                    min_cost = cost
                    best_path = [city] + sub_path

        return min_cost, best_path

    min_cost, path = dp(1, 0)

    full_path = [0] + path
    path_with_prefix = [f"p{i}" for i in full_path]

    return min_cost, path_with_prefix


def print_clean_route(places_dict, optimal_path, min_route_time_dist_dict, dim):
    
    # Step 1: Convert keys to actual place strings
    raw_places = [places_dict[p] for p in optimal_path]

    # Step 2: Replace + with space
    places = [p.replace("+", " ") for p in raw_places]

    # Step 3: Split by comma
    split_places = [p.split(",") for p in places]
    split_places = [[part.strip() for part in place] for place in split_places]

    # Step 4: Find common suffix
    reversed_parts = [list(reversed(place)) for place in split_places]

    common_suffix = []
    for parts in zip(*reversed_parts):
        if all(part == parts[0] for part in parts):
            common_suffix.append(parts[0])
        else:
            break

    suffix_len = len(common_suffix)

    # Step 5: Remove common suffix
    cleaned_places = []
    for place in split_places:
        if suffix_len > 0:
            cleaned = place[:-suffix_len]
        else:
            cleaned = place
        cleaned_places.append(cleaned[0])

    # Step 6: Build route with distance
    route_parts = []

    for i in range(len(optimal_path) - 1):
        start = optimal_path[i]
        end = optimal_path[i + 1]

        value = min_route_time_dist_dict.get(f"{start}/{end}", 0)
        route_parts.append(f"{cleaned_places[i]} -{value} {dim}->")

    route_parts.append(cleaned_places[-1])

    return " ".join(route_parts)


def open_maps_in_browser(url):
    driver = webdriver.Chrome()
    driver.get(url)

    input("To exit press ctrl+c and close browser\n")
    driver.quit()


def create_gmap_urls(places_dict, optimal_path, max_places=10):
    urls = []

    # step size keeps overlap so route continues correctly
    step = max_places - 1

    for i in range(0, len(optimal_path)-1, step):
        chunk = optimal_path[i:i + max_places]

        route_string = "/".join(places_dict[p] for p in chunk)
        url = f"https://www.google.com/maps/dir/{route_string}"

        urls.append(url)

        if i + max_places >= len(optimal_path):
            break

    return urls


def main(gmap_url=["https://www.google.com/maps/dir/Ramky+One+Kosmos,+Eco+Art+Studio,+Ramky+One+Kosmos+Rd,+Tellapur,+Hyderabad,+Nallagandla,+Telangana+500046/Shah+Ghouse+Hotel+%26+Restaurant,+Gachibowli,+Villa-8,+Gachibowli+Rd,+opposite+Bio+Diversity+Park,+Raidurgam,+Madhura+Nagar+Colony,+Gachibowli,+Hyderabad,+Telangana+500104/Golconda+Fort,+Hyderabad,+Telangana/Micron+Technology+Aquila,+Phoenix+-+Aquila+Block+A+Financial+District,+Nankaramguda,+Serilingampalle+(M),+Hyderabad,+Telangana+500032/@17.4187615,78.313202,13z/data=!3m1!4b1!4m26!4m25!1m5!1m1!1s0x3bcb9327b3c2efe1:0xfd50a105df6e72e!2m2!1d78.3045696!2d17.4617084!1m5!1m1!1s0x3bcb93f96a9c5151:0xc3acabf7b492dc17!2m2!1d78.3762853!2d17.4267841!1m5!1m1!1s0x3bcb968c5f1342f3:0xd752a9bdbdde84df!2m2!1d78.4033392!2d17.3847636!1m5!1m1!1s0x3bcb95b81f90ab95:0xd3005ecbfbd05f8b!2m2!1d78.340366!2d17.4173728!3e9?entry=ttu&g_ep=EgoyMDI2MDMwNC4xIKXMDSoASAFQAw%3D%3D"
      , "https://www.google.com/maps/dir/Shubam+Royal+Apartments,+Friends+Colony,+Puppal+Guda,+Qutub+Shahi+Tombs,+Hyderabad,+Manikonda,+Telangana+500089,+India/Manikonda+Sub+Post+Office,+C92G%2BVVX,+Manikonda+Garden,+Sri+Balaji+Nagar+Colony,+Hyderabad,+Telangana+500089/Babai+Hotel+Manikonda,+G7,+G8,+C92Q%2BCHM,+Old+Tharuni+Super+Market,+Aashritha+Meadows,+Shaikpet+Main+Rd,+beside+SBI,+Dream+Valley,+Tanasha+Nagar,+Puppalguda,+Hyderabad,+Manikonda,+Telangana+500089/Mehfil+Restaurant,+Whisper+Valley+Road,+Narne+Road,+opp.+JRC+Conventional+Center,+Shaikpet,+Hyderabad,+Telangana+500104/@17.4084592,78.3758072,15z/data=!3m1!4b1!4m25!4m24!1m5!1m1!1s0x3bcb96a2120955f1:0xf5c3c4f4b0c80b07!2m2!1d78.39105!2d17.3999503!1m5!1m1!1s0x3bcb94193d6d70eb:0x3466d46b83cdf94b!2m2!1d78.3772435!2d17.4022336!1m5!1m1!1s0x3bcb977cfa74a4ed:0x977c30fccd1c8b89!2m2!1d78.3883722!2d17.4005477!1m5!1m1!1s0x3bcb96ae37b2744b:0x27a0b4efcb901e4a!2m2!1d78.3942405!2d17.4144473?entry=ttu&g_ep=EgoyMDI2MDMwNC4xIKXMDSoASAFQAw%3D%3D"]
      , optimize_by=['time', 'dist']):
    # -----------------------------
    # 1. Load places
    # -----------------------------
    places_dict = create_places_dict(gmap_url)
    # places_dict = load_places_from_file(places_fullfilepath)
    # print(places_dict) #{'p0': 'Aparna+Cyberscape+A+Block', 'p1': 'Aparna+CyberZon+Block+J'}

    # -----------------------------
    # 2. Generate route URLs
    # -----------------------------
    route_url_dict = create_route_url_dict(places_dict)
    # print(route_url_dict) #{'p0/p1': 'https://www.google.com/maps/dir/Aparna+Cyberscape+A+Block/Aparna+CyberZon+Block+J', 'p1/p0': 'https://www.google.com/maps/dir/Aparna+CyberZon+Block+J/Aparna+Cyberscape+A+Block'}

    # -----------------------------
    # 3. Scrape time & distance
    # -----------------------------
    raw_route_time_dist_dict = scrape_in_batches(route_url_dict, batch_size=30)
    # print(raw_route_time_dist_dict) #{'p0/p1': ['12 min', '9 min', '25 min', '25 min', '1.8 km', '31 min', '2.3 km'], 'p1/p0': ['13 min', '10 min', '25 min', '25 min', '1.8 km', '27 min', '2.0 km', '33 min', '2.4 km']}

    # -----------------------------
    # 4. Extract valid time-distance pairs
    # -----------------------------
    route_time_dist_dict = valid_time_dist_pairs(raw_route_time_dist_dict)
    # print(route_time_dist_dict) #{'p0/p1': [('25 min', '1.8 km'), ('31 min', '2.3 km')], 'p1/p0': [('25 min', '1.8 km'), ('27 min', '2.0 km'), ('33 min', '2.4 km')]}

    for param in optimize_by:
        if param == 'dist':
            dim = 'km'
        else:
            dim = 'mi'
        # -----------------------------
        # 5. Get minimum route distances
        # -----------------------------
        min_route_time_dist_dict = min_route_time_dist(route_time_dist_dict, param)
        # print(min_route_time_dist_dict) #{'p0/p1': 1800, 'p1/p0': 1800}

        # -----------------------------
        # 6. Create distance matrix
        # -----------------------------
        matrix, places = create_matrix(min_route_time_dist_dict, places_dict)
        # print(matrix)

        # -----------------------------
        # 7. Solve TSP
        # -----------------------------
        min_cost, path = solve_tsp_with_path(matrix)
        optimal_path = [places[int(p[1:])] for p in path]
        print(f"\n{param} - min cost:\n{min_cost} {dim}") #3600

        # -----------------------------
        # 8. Print clean route
        # -----------------------------
        final_route = print_clean_route(places_dict, optimal_path, min_route_time_dist_dict, dim)
        print(f"\n{param} - final route:\n{final_route}\n") #Aparna Cyberscape A Block -1800-> Aparna CyberZon Block J -1800-> Aparna Cyberscape A Block

        # -----------------------------
        # 9. Open final Google Maps route
        # -----------------------------
        url = create_gmap_urls(places_dict, optimal_path)
        print(f"{param} - open gmaps url: ctrl + click:\n{url}\n") #https://www.google.com/maps/dir/Aparna+Cyberscape+A+Block/Aparna+CyberZon+Block+J/Aparna+Cyberscape+A+Block

    open_maps_in_browser(url[0])
