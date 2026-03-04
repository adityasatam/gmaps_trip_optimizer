from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import defaultdict
from functools import lru_cache
import re
import time
import os
import sys


# def create_silent_driver():
#     options = Options()

#     # Disable Chrome logging
#     options.add_argument("--log-level=3")
#     options.add_argument("--disable-logging")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--disable-extensions")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")

#     # Remove "DevTools listening"
#     options.add_experimental_option("excludeSwitches", ["enable-logging"])

#     # Silence chromedriver service logs
#     service = Service(log_path=os.devnull)

#     # Suppress stderr completely (strong suppression)
#     sys.stderr = open(os.devnull, 'w')

#     driver = webdriver.Chrome(service=service, options=options)
#     return driver


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

        # time.sleep(3)

        # elements = driver.find_elements(
        #     By.XPATH,
        #     "//div[contains(text(),'hr') or contains(text(),'min') or contains(text(),'h') or contains(text(),'m') or contains(text(),'km')]"
        # )

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


def min_route_time_dist(route_time_dist_dict):
    min_route_time_dist_dict = {}

    for route, pairs in route_time_dist_dict.items():
        grouped = defaultdict(list)

        for time_str, dist_str in pairs:
            time_min = convert_time_to_mins(time_str)
            dist_m = convert_dist_to_mtrs(dist_str)
            grouped[dist_m].append(time_min)

        if grouped:
            min_distance = min(grouped.keys())
            min_route_time_dist_dict[route] = min_distance
        else:
            min_route_time_dist_dict[route] = None  # or 0

    return min_route_time_dist_dict


def create_dist_matrix(min_route_time_dist_dict):
    # Step 1: Extract unique places
    places = sorted(
        set(p for key in min_route_time_dist_dict for p in key.split('/'))
    )

    n = len(places)

    # Step 2: Create empty matrix
    dist_matrix = [[0] * n for _ in range(n)]

    # Step 3: Map place to index
    index = {place: i for i, place in enumerate(places)}

    # Step 4: Fill matrix directly (no mirroring)
    for key, value in min_route_time_dist_dict.items():
        p1, p2 = key.split('/')
        i = index[p1]
        j = index[p2]

        dist_matrix[i][j] = value   # fill only this direction

    return dist_matrix


def solve_tsp_with_path(dist_matrix):
    n = len(dist_matrix)

    parent = {}

    @lru_cache(None)
    def dp(mask, pos):
        if mask == (1 << n) - 1:
            return dist_matrix[pos][0]

        min_cost = float('inf')
        best_city = -1

        for city in range(n):
            if not (mask & (1 << city)):
                cost = dist_matrix[pos][city] + dp(mask | (1 << city), city)
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


def print_clean_route(places_dict, optimal_path):
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

    # Step 6: Print final route
    final_route = " -> ".join(cleaned_places)
    print(f"\nfinal_route:\n{final_route}\n")


def open_maps_in_browser(url):
    driver = webdriver.Chrome()
    driver.get(url)

    input("To exit press ctrl+c and close browser\n")
    driver.quit()


def create_and_open_maps_url(places_dict, optimal_path, max_places=10):
    if len(optimal_path) > max_places:
        optimal_path = optimal_path[0:9] + [optimal_path[-1]]

    route_string = "/".join(places_dict[p] for p in optimal_path)

    url = f"https://www.google.com/maps/dir/{route_string}"

    print(f"open gmaps url: ctrl + click:\n{url}\n")
    open_maps_in_browser(url)


def main(file_path=r"C:/Users/sasuk/travelling_salesman/", file_name="sample_destinations.txt"):
    places_fullfilepath = file_path+file_name
    # -----------------------------
    # 1. Load places
    # -----------------------------
    places_dict = load_places_from_file(places_fullfilepath)

    # -----------------------------
    # 2. Generate route URLs
    # -----------------------------
    route_url_dict = create_route_url_dict(places_dict)

    # -----------------------------
    # 3. Scrape time & distance
    # -----------------------------
    raw_route_time_dist_dict = scrape_time_dist_from_gmaps(route_url_dict)
    # print(raw_route_time_dist_dict)
    # -----------------------------
    # 4. Extract valid time-distance pairs
    # -----------------------------
    route_time_dist_dict = valid_time_dist_pairs(raw_route_time_dist_dict)
    # print(route_time_dist_dict)

    # -----------------------------
    # 5. Get minimum route distances
    # -----------------------------
    min_route_time_dist_dict = min_route_time_dist(route_time_dist_dict)
    # print(min_route_time_dist_dict)

    # -----------------------------
    # 6. Create distance matrix
    # -----------------------------
    dist_matrix = create_dist_matrix(min_route_time_dist_dict)
    # print(dist_matrix)
    # -----------------------------
    # 7. Solve TSP
    # -----------------------------
    min_cost, optimal_path = solve_tsp_with_path(dist_matrix)
    print(min_cost)

    # -----------------------------
    # 8. Print clean route
    # -----------------------------
    print_clean_route(places_dict, optimal_path)

    # -----------------------------
    # 9. Open final Google Maps route
    # -----------------------------
    create_and_open_maps_url(places_dict, optimal_path)
