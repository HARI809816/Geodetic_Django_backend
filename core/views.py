from django.http import JsonResponse
import numpy as np
import os
from django.http import HttpResponse  
from collections import defaultdict
from django.conf import settings



# -------- Folder where files exist --------
#DATA_DIR = "./data"  
DATA_DIR = os.path.join(settings.BASE_DIR, "core", "data") # put all .stacov files here

# -------- WGS84 constants --------
a = 6378137.0
f = 1 / 298.257223563
e2 = 2*f - f*f

# -------- ECEF → LLA --------
def ecef_to_lla_np(X, Y, Z):
    lon = np.arctan2(Y, X)
    p = np.sqrt(X**2 + Y**2)
    lat = np.arctan2(Z, p * (1 - e2))

    for _ in range(5):
        N = a / np.sqrt(1 - e2 * np.sin(lat)**2)
        h = p / np.cos(lat) - N
        lat = np.arctan2(Z, p * (1 - e2 * N / (N + h)))

    N = a / np.sqrt(1 - e2 * np.sin(lat)**2)
    h = p / np.cos(lat) - N

    return float(np.degrees(lat)), float(np.degrees(lon)), float(h)

# -------- API --------



def get_stations_by_date(request, date):
    """
    date format: 24apr18
    """
    print(date)
    filename = f"{date}NOAM4.0_ambres_nfx20.stacov"
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        return JsonResponse(
            {
                "error": f"File not found for date {date}"
            },
            status=404
        )

    stations = defaultdict(dict)

    with open(filepath, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 6:
                continue
            if parts[2] == "STA":
                station = parts[1]
                axis = parts[3]  # X, Y, Z
                stations[station][axis] = float(parts[4])

    features = []

    for station, c in stations.items():
        if {"X", "Y", "Z"} <= c.keys():
            lat, lon, h = ecef_to_lla_np(c["X"], c["Y"], c["Z"])

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        round(lon, 8),
                        round(lat, 8)
                    ]
                },
                "properties": {
                    "station": station,
                    "latitude": round(lat, 6),     
                     "longitude": round(lon, 6),
                    "height_m": round(h, 3),
                    "date": date
                }
            })

    return JsonResponse({
        "type": "FeatureCollection",
        "station_count": len(features),
        "features": features
    },safe=False)
