import math
import re
import unicodedata

import polyline
import requests

def get_travel_speed_kmh(mode):
    speeds = {
        "walking": 5,
        "cycling": 28,
        "driving": 35,
    }
    return speeds.get(mode, 35)
    
def estimate_duration_minutes(distance_km, mode="driving"):
    if distance_km <= 0:
        return 0

    duration_min = round((distance_km / get_travel_speed_kmh(mode)) * 60)
    return max(duration_min, 1)


def haversine_distance_km(start_lat, start_lng, end_lat, end_lng):
    earth_radius_km = 6371.0
    lat1 = math.radians(float(start_lat))
    lng1 = math.radians(float(start_lng))
    lat2 = math.radians(float(end_lat))
    lng2 = math.radians(float(end_lng))

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c



class GISSearchTool:
    def __init__(self):
        self.geocode_url = "https://nominatim.openstreetmap.org/search"
        self.reverse_geocode_url = "https://nominatim.openstreetmap.org/reverse"
        self.headers = {"User-Agent": "MyGISApp/1.0"}

    @staticmethod
    def normalize_radius_value(raw_value):
        try:
            value = int(float(raw_value))
        except (TypeError, ValueError):
            value = 5

        return max(5, min(30, value))

    @staticmethod
    def normalize_search_text(value):
        text = (value or "").casefold().replace("đ", "d")
        text = unicodedata.normalize("NFD", text)
        text = "".join(char for char in text if unicodedata.category(char) != "Mn")
        text = re.sub(r"[^a-z0-9]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def mode_label(mode):
        labels = {
            "driving": "\u00f4 t\u00f4",
            "cycling": "xe m\u00e1y",
            "walking": "\u0111i b\u1ed9",
        }
        return labels.get(mode, "\u00f4 t\u00f4")

    def build_search_aliases(self, keyword):
        normalized_keyword = self.normalize_search_text(keyword)
        if not normalized_keyword:
            return set()

        aliases = {normalized_keyword, normalized_keyword.replace(" ", "")}

        district_match = re.search(r"\b(?:quan|q)\s*(\d+)\b", normalized_keyword)
        if district_match:
            district_number = district_match.group(1)
            aliases.update(
                {
                    f"quan {district_number}",
                    f"q {district_number}",
                    f"quan{district_number}",
                    f"q{district_number}",
                }
            )

        ward_match = re.search(r"\b(?:phuong|p)\s*([a-z0-9]+)\b", normalized_keyword)
        if ward_match:
            ward_value = ward_match.group(1)
            aliases.update(
                {
                    f"phuong {ward_value}",
                    f"p {ward_value}",
                    f"phuong{ward_value}",
                    f"p{ward_value}",
                }
            )

        if "thu duc" in normalized_keyword:
            aliases.update({"thu duc", "tp thu duc", "thanh pho thu duc"})

        return {alias.strip() for alias in aliases if alias.strip()}

    def get_textual_matches(self, keyword, apartments_db):
        aliases = self.build_search_aliases(keyword)
        if not aliases:
            return []

        matches = []
        for apt in apartments_db:
            normalized_address = self.normalize_search_text(apt.address)
            normalized_name = self.normalize_search_text(apt.name)
            compact_address = normalized_address.replace(" ", "")
            compact_name = normalized_name.replace(" ", "")
            score = 0

            for alias in aliases:
                compact_alias = alias.replace(" ", "")
                if alias in normalized_address or compact_alias in compact_address:
                    score = max(score, 3)
                elif alias in normalized_name or compact_alias in compact_name:
                    score = max(score, 2)

            if score:
                matches.append((score, apt))

        matches.sort(key=lambda item: (-item[0], item[1].id))
        return [apt for _, apt in matches]

    def minutes_to_distance_km(self, minutes, mode="driving"):
        normalized_minutes = self.normalize_radius_value(minutes)
        return round((normalized_minutes / 60) * get_travel_speed_kmh(mode), 2)

    def search_locations(self, keyword, limit=5):
        params = {
            "q": keyword,
            "format": "json",
            "limit": limit,
            "addressdetails": 1,
        }

        res = requests.get(self.geocode_url, params=params, headers=self.headers, timeout=5)
        data = res.json()

        results = []
        for item in data:
            results.append(
                {
                    "name": item.get("display_name", ""),
                    "lat": float(item["lat"]),
                    "lng": float(item["lon"]),
                }
            )
        return results

    def reverse_geocode(self, lat, lng):
        params = {
            "lat": lat,
            "lon": lng,
            "format": "jsonv2",
            "addressdetails": 1,
        }

        res = requests.get(self.reverse_geocode_url, params=params, headers=self.headers, timeout=5)
        data = res.json()
        return {
            "address": (data.get("display_name") or "").strip(),
            "lat": float(data.get("lat", lat)),
            "lng": float(data.get("lon", lng)),
        }

    def get_apartments_in_region(self, keyword, apartments_db):
        textual_matches = self.get_textual_matches(keyword, apartments_db)
        textual_ids = {apt.id for apt in textual_matches}
        params = {
            "q": f"{keyword}, TP.HCM, Viet Nam",
            "format": "json",
            "limit": 1,
        }

        try:
            res = requests.get(self.geocode_url, params=params, headers=self.headers, timeout=5)
            data = res.json()

            if data:
                bbox = data[0]["boundingbox"]
                lat_min, lat_max = float(bbox[0]), float(bbox[1])
                lon_min, lon_max = float(bbox[2]), float(bbox[3])

                valid_apartments = []
                for apt in apartments_db:
                    if (lat_min <= apt.lat <= lat_max) and (lon_min <= apt.lng <= lon_max):
                        valid_apartments.append(apt)

                if valid_apartments and textual_matches:
                    narrowed_results = [apt for apt in valid_apartments if apt.id in textual_ids]
                    if narrowed_results:
                        return narrowed_results

                if textual_matches:
                    return textual_matches

                if valid_apartments:
                    return valid_apartments
        except Exception:
            pass

        return textual_matches

    def get_apartments_near_location(
        self,
        lat,
        lng,
        apartments_db,
        criteria="distance",
        value=5,
        mode="driving",
    ):
        criteria = criteria if criteria in {"distance", "time"} else "distance"
        normalized_value = self.normalize_radius_value(value)
        mode = mode if mode in {"driving", "cycling", "walking"} else "driving"
        search_radius_km = (
            self.minutes_to_distance_km(normalized_value, mode)
            if criteria == "time"
            else float(normalized_value)
        )

        nearby_results = []
        speed_kmh = get_travel_speed_kmh(mode)
        for apt in apartments_db:
            distance_km = haversine_distance_km(lat, lng, apt.lat, apt.lng)
            raw_minutes = 0 if distance_km <= 0 else (distance_km / speed_kmh) * 60
            estimated_time_min = estimate_duration_minutes(distance_km, mode)

            is_match = (
                distance_km <= search_radius_km
                if criteria == "distance"
                else raw_minutes <= normalized_value
            )
            if not is_match:
                continue

            nearby_results.append(
                {
                    "apartment": apt,
                    "distance_km": round(distance_km, 2),
                    "estimated_time_min": estimated_time_min,
                }
            )

        nearby_results.sort(key=lambda item: (item["distance_km"], item["apartment"].id))
        return {
            "results": nearby_results,
            "search_radius_km": round(search_radius_km, 2),
            "criteria": criteria,
            "value": normalized_value,
            "mode": mode,
            "mode_label": self.mode_label(mode),
        }
