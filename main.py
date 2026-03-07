from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from functools import lru_cache
import re


def load_places_from_file(file_path):
    places_dict = {}

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):   # start from 0
        place = line.strip()
        if place:
            places_dict[f"p{idx}"] = place.replace(" ", "+")

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


def convert_dist_to_mtrs(dist_str):
    dist_str = dist_str.lower().strip()

    km_match = re.search(r'(\d+(?:\.\d+)?)\s*km\b', dist_str)
    m_match = re.search(r'(\d+)\s*m\b', dist_str)

    if km_match:
        return float(km_match.group(1)) * 1000

    if m_match:
        return float(m_match.group(1))

    return 0


def min_route_time_dist(route_time_dist_dict, param):
    min_route_time_dist_dict = {}

    for route, pairs in route_time_dist_dict.items():

        times = []
        dists = []

        for time_str, dist_str in pairs:
            time_min = convert_time_to_mins(time_str)
            dist_m = convert_dist_to_mtrs(dist_str)

            times.append(time_min)
            dists.append(dist_m)

        if param == "dist":
            min_route_time_dist_dict[route] = min(dists) if dists else None

        elif param == "time":
            min_route_time_dist_dict[route] = min(times) if times else None

        else:
            raise ValueError("param must be 'dist' or 'time'")

    return min_route_time_dist_dict


def create_matrix(min_route_time_dist_dict):
    # Step 1: Extract unique places
    places = sorted(
        set(p for key in min_route_time_dist_dict for p in key.split('/'))
    )

    n = len(places)

    # Step 2: Create empty matrix
    matrix = [[0] * n for _ in range(n)]

    # Step 3: Map place to index
    index = {place: i for i, place in enumerate(places)}

    # Step 4: Fill matrix directly (no mirroring)
    for key, value in min_route_time_dist_dict.items():
        p1, p2 = key.split('/')
        i = index[p1]
        j = index[p2]

        matrix[i][j] = value   # fill only this direction

    return matrix


def solve_tsp_with_path(matrix):
    n = len(matrix)

    parent = {}

    @lru_cache(None)
    def dp(mask, pos):
        if mask == (1 << n) - 1:
            return matrix[pos][0]

        min_cost = float('inf')
        best_city = -1

        for city in range(n):
            if not (mask & (1 << city)):
                cost = matrix[pos][city] + dp(mask | (1 << city), city)
                if cost < min_cost:
                    min_cost = cost
                    best_city = city

        parent[(mask, pos)] = best_city
        return min_cost

    min_cost = dp(1, 0)

    # Reconstruct Path
    mask = 1
    pos = 0
    path = [0]

    while mask != (1 << n) - 1:
        next_city = parent[(mask, pos)]
        path.append(next_city)
        mask |= (1 << next_city)
        pos = next_city

    path.append(0)  # return to start

    path_with_prefix = [f"p{city}" for city in path]

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

        distance = int(min_route_time_dist_dict.get(f"{start}/{end}", 0))

        route_parts.append(f"{cleaned_places[i]} -{distance} {dim}->")

    route_parts.append(cleaned_places[-1])

    return " ".join(route_parts)


def open_maps_in_browser(url):
    driver = webdriver.Chrome()
    driver.get(url)

    input("To exit press ctrl+c and close browser\n")
    driver.quit()


def create_gmap_url(places_dict, optimal_path, max_places=10):
    if len(optimal_path) > max_places:
        optimal_path = optimal_path[0:9] + [optimal_path[-1]]

    route_string = "/".join(places_dict[p] for p in optimal_path)

    url = f"https://www.google.com/maps/dir/{route_string}"

    return url


def main(file_path=r"C:/Users/sasuk/travelling_salesman/", file_name="sample_destinations.txt", parameters=['time', 'dist']):
    places_fullfilepath = file_path+file_name
    # -----------------------------
    # 1. Load places
    # -----------------------------
    places_dict = load_places_from_file(places_fullfilepath)
    # print(places_dict) #{'p0': 'Aparna+Cyberscape+A+Block', 'p1': 'Aparna+CyberZon+Block+J'}

    # -----------------------------
    # 2. Generate route URLs
    # -----------------------------
    route_url_dict = create_route_url_dict(places_dict)
    # print(route_url_dict) #{'p0/p1': 'https://www.google.com/maps/dir/Aparna+Cyberscape+A+Block/Aparna+CyberZon+Block+J', 'p1/p0': 'https://www.google.com/maps/dir/Aparna+CyberZon+Block+J/Aparna+Cyberscape+A+Block'}

    # -----------------------------
    # 3. Scrape time & distance
    # -----------------------------
    raw_route_time_dist_dict = scrape_time_dist_from_gmaps(route_url_dict)
    # print(raw_route_time_dist_dict) #{'p0/p1': ['12 min', '9 min', '25 min', '25 min', '1.8 km', '31 min', '2.3 km'], 'p1/p0': ['13 min', '10 min', '25 min', '25 min', '1.8 km', '27 min', '2.0 km', '33 min', '2.4 km']}

    # -----------------------------
    # 4. Extract valid time-distance pairs
    # -----------------------------
    route_time_dist_dict = valid_time_dist_pairs(raw_route_time_dist_dict)
    # print(route_time_dist_dict) #{'p0/p1': [('25 min', '1.8 km'), ('31 min', '2.3 km')], 'p1/p0': [('25 min', '1.8 km'), ('27 min', '2.0 km'), ('33 min', '2.4 km')]}

    for param in parameters:
        if param == 'dist':
            dim = 'mtr'
        else:
            dim = 'min'
        # -----------------------------
        # 5. Get minimum route distances
        # -----------------------------
        min_route_time_dist_dict = min_route_time_dist(route_time_dist_dict, param)
        # print(min_route_time_dist_dict) #{'p0/p1': 1800.0, 'p1/p0': 1800.0}

        # -----------------------------
        # 6. Create distance matrix
        # -----------------------------
        matrix = create_matrix(min_route_time_dist_dict)
        # print(matrix)

        # -----------------------------
        # 7. Solve TSP
        # -----------------------------
        min_cost, optimal_path = solve_tsp_with_path(matrix)
        print(f"\n{param} - min cost:\n{min_cost} {dim}") #3600.0

        # -----------------------------
        # 8. Print clean route
        # -----------------------------
        final_route = print_clean_route(places_dict, optimal_path, min_route_time_dist_dict, dim)
        print(f"\n{param} - final route:\n{final_route}\n") #Aparna Cyberscape A Block -1800-> Aparna CyberZon Block J -1800-> Aparna Cyberscape A Block

        # -----------------------------
        # 9. Open final Google Maps route
        # -----------------------------
        url = create_gmap_url(places_dict, optimal_path)
        print(f"{param} - open gmaps url: ctrl + click:\n{url}\n") #https://www.google.com/maps/dir/Aparna+Cyberscape+A+Block/Aparna+CyberZon+Block+J/Aparna+Cyberscape+A+Block

    open_maps_in_browser(url)
