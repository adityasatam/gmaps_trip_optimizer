from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from collections import defaultdict
from functools import lru_cache
import re
import time
import os
import sys


def create_silent_driver():
    options = Options()

    # Disable Chrome logging
    options.add_argument("--log-level=3")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Remove "DevTools listening"
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # Silence chromedriver service logs
    service = Service(log_path=os.devnull)

    # Suppress stderr completely (strong suppression)
    sys.stderr = open(os.devnull, 'w')

    driver = webdriver.Chrome(service=service, options=options)
    return driver


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
    #driver = webdriver.Chrome()
    driver = create_silent_driver()
    raw_route_time_dist_dict = {}

    for route_key, route_url in route_url_dict.items():
        driver.get(route_url)
        time.sleep(5)

        elements = driver.find_elements(
            By.XPATH,
            "//div[contains(text(),'hr') or contains(text(),'min') or contains(text(),'km') or contains(text(),'m')]"
        )

        pattern = re.compile(
            r"\d+\s*h(?:\s*\d+\s*m)?|"
            r"\d+\s*hr(?:\s*\d+\s*min)?|"
            r"\d+\s*min|"
            r"\d+(?:\.\d+)?\s*km|"
            r"\d+\s*m"
        )

        extracted_values = []

        for el in elements:
            matches = pattern.findall(el.text)
            for match in matches:
                extracted_values.append(match.strip())

        raw_route_time_dist_dict[route_key] = extracted_values

    driver.quit()
    return raw_route_time_dist_dict


def valid_time_dist_pairs(raw_route_time_dist_dict):
    distance_regex = re.compile(r'\b\d+(?:\.\d+)?\s+(?:km|m)\b')
    route_time_dist_dict = {}

    for route_key, values in raw_route_time_dist_dict.items():
        start_index = None

        for i, val in enumerate(values):
            if distance_regex.search(val):
                start_index = i - 1
                break

        route_time_dist_dict[route_key] = values[start_index:] if start_index is not None else []

    return route_time_dist_dict


def convert_time_to_mins(time_str):
    hr_match = re.search(r'(\d+)\s*hr', time_str)
    min_match = re.search(r'(\d+)\s*min', time_str)

    hours = int(hr_match.group(1)) if hr_match else 0
    minutes = int(min_match.group(1)) if min_match else 0

    return hours * 60 + minutes


def convert_dist_to_mtrs(dist_str):
    if 'km' in dist_str:
        return float(dist_str.replace(' km', '')) * 1000
    elif 'm' in dist_str:
        return float(dist_str.replace(' m', ''))
    return 0


def min_route_time_dist(route_time_dist_dict):
    min_route_time_dist_dict= {}

    for k, v in route_time_dist_dict.items():
        # ------------------------
        # Step 3: Normalize + group
        # ------------------------

        grouped = defaultdict(list)

        for i in range(0, len(v), 2):
            time_min = convert_time_to_mins(v[i])
            dist_m = convert_dist_to_mtrs(v[i+1])
            grouped[dist_m].append(time_min)

        # ------------------------
        # Step 4: Find min distance
        # ------------------------

        min_distance = min(grouped.keys())
        # min_time = min(grouped[min_distance])

        min_route_time_dist_dict[k] = min_distance

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
    driver = create_silent_driver()
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
    print(places_dict)

    # -----------------------------
    # 2. Generate route URLs
    # -----------------------------
    route_url_dict = create_route_url_dict(places_dict)

    # -----------------------------
    # 3. Scrape time & distance
    # -----------------------------
    raw_route_time_dist_dict = scrape_time_dist_from_gmaps(route_url_dict)

    # -----------------------------
    # 4. Extract valid time-distance pairs
    # -----------------------------
    route_time_dist_dict = valid_time_dist_pairs(raw_route_time_dist_dict)

    # -----------------------------
    # 5. Get minimum route distances
    # -----------------------------
    min_route_time_dist_dict = min_route_time_dist(route_time_dist_dict)

    # -----------------------------
    # 6. Create distance matrix
    # -----------------------------
    dist_matrix = create_dist_matrix(min_route_time_dist_dict)

    # -----------------------------
    # 7. Solve TSP
    # -----------------------------
    min_cost, optimal_path = solve_tsp_with_path(dist_matrix)

    # -----------------------------
    # 8. Print clean route
    # -----------------------------
    print_clean_route(places_dict, optimal_path)

    # -----------------------------
    # 9. Open final Google Maps route
    # -----------------------------
    create_and_open_maps_url(places_dict, optimal_path)
