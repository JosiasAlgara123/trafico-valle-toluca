import os
import csv
import requests
from datetime import datetime
import pytz

TOMTOM_API_KEY = os.environ.get("TOMTOM_API_KEY")

# 17 nodos estratégicos de la Zona Metropolitana del Valle de Toluca
NODOS_TOLUCA = [
    {"id": "TOLLOCAN_PILARES", "nombre": "Paseo Tollocan - Pilares", "lat": 19.2869, "lon": -99.6094},
    {"id": "TOLLOCAN_TERMINAL", "nombre": "Paseo Tollocan - Terminal", "lat": 19.2797, "lon": -99.6433},
    {"id": "TOLLOCAN_COLON", "nombre": "Paseo Tollocan - Paseo Colon", "lat": 19.2768, "lon": -99.6562},
    {"id": "TOLLOCAN_CRIN", "nombre": "Paseo Tollocan - Santa Elena / San Mateo", "lat": 19.2831, "lon": -99.5562},
    {"id": "TOLLOCAN_COMONFORT", "nombre": "Paseo Tollocan - Comonfort", "lat": 19.2849, "lon": -99.6258},
    {"id": "TORRES_PINO_SUAREZ", "nombre": "Solidaridad Las Torres - Pino Suarez", "lat": 19.2683, "lon": -99.6392},
    {"id": "TORRES_TECNOLOGICO", "nombre": "Solidaridad Las Torres - Tecnologico", "lat": 19.2665, "lon": -99.5968},
    {"id": "TORRES_DIAZ_MIRON", "nombre": "Solidaridad Las Torres - Diaz Miron", "lat": 19.2712, "lon": -99.6224},
    {"id": "LOPEZ_MATEOS_CU", "nombre": "Adolfo Lopez Mateos - CU", "lat": 19.2836, "lon": -99.6766},
    {"id": "LOPEZ_MATEOS_ZINA", "nombre": "Adolfo Lopez Mateos - Zinacantepec", "lat": 19.2858, "lon": -99.7135},
    {"id": "CARRANZA_CU", "nombre": "Venustiano Carranza - CU / Vicente Guerrero", "lat": 19.2804, "lon": -99.6698},
    {"id": "PINO_SUAREZ_METEPEC", "nombre": "Pino Suarez - Limite Metepec", "lat": 19.2618, "lon": -99.6358},
    {"id": "MORELOS_CENTRO", "nombre": "Jose Maria Morelos - Centro", "lat": 19.2891, "lon": -99.6548},
    {"id": "BLVD_AEROPUERTO", "nombre": "Boulevard Aeropuerto - Plaza Sendero", "lat": 19.3039, "lon": -99.5750},
    {"id": "LERMA_INDUSTRIAL", "nombre": "Carretera Mexico-Toluca - Lerma", "lat": 19.2852, "lon": -99.5132},
    {"id": "TECH_METEPEC", "nombre": "Av. Tecnologico - Metepec", "lat": 19.2602, "lon": -99.5960},
    {"id": "ALFREDO_DEL_MAZO", "nombre": "Alfredo del Mazo - Tres Caminos", "lat": 19.3145, "lon": -99.6391}
]

ARCHIVO_CSV = "trafico_toluca.csv"

def obtener_clima_toluca():
    url = "https://api.open-meteo.com/v1/forecast?latitude=19.2826&longitude=-99.6557&current=temperature_2m,precipitation,weather_code"
    try:
        r = requests.get(url, timeout=10).json()
        current = r.get("current", {})
        return {
            "temp_c": current.get("temperature_2m", 0),
            "precipitacion_mm": current.get("precipitation", 0),
            "codigo_clima": current.get("weather_code", 0)
        }
    except Exception:
        return {"temp_c": None, "precipitacion_mm": None, "codigo_clima": None}

def clasificar_congestion(vel_actual, vel_libre):
    if not vel_libre or vel_libre == 0:
        return -1
    ratio = vel_actual / vel_libre
    if ratio >= 0.80:
        return 0
    elif ratio >= 0.50:
        return 1
    elif ratio >= 0.25:
        return 2
    else:
        return 3

def main():
    tz_mexico = pytz.timezone("America/Mexico_City")
    ahora = datetime.now(tz_mexico)
    clima = obtener_clima_toluca()

    archivo_existe = os.path.isfile(ARCHIVO_CSV)
    columnas = [
        "timestamp", "fecha", "hora", "dia_semana", "es_fin_semana", "es_quincena",
        "nodo_id", "nodo_nombre", "lat", "lon",
        "velocidad_actual_kmh", "velocidad_libre_kmh", "tiempo_actual_seg",
        "tiempo_libre_seg", "ratio_velocidad", "confianza_dato",
        "temp_c", "precipitacion_mm", "codigo_clima", "nivel_congestion"
    ]

    with open(ARCHIVO_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        if not archivo_existe:
            writer.writeheader()

        for nodo in NODOS_TOLUCA:
            url = (
                f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
                f"?point={nodo['lat']},{nodo['lon']}&unit=KMPH&openLr=false&key={TOMTOM_API_KEY}"
            )
            try:
                resp = requests.get(url, timeout=10).json()
                data = resp.get("flowSegmentData", {})
                vel_actual = data.get("currentSpeed", 0)
                vel_libre = data.get("freeFlowSpeed", 0)
                t_actual = data.get("currentTravelTime", 0)
                t_libre = data.get("freeFlowTravelTime", 0)
                confianza = data.get("confidence", 0)

                ratio = round(vel_actual / vel_libre, 4) if vel_libre else 0
                clase = clasificar_congestion(vel_actual, vel_libre)

                writer.writerow({
                    "timestamp": ahora.isoformat(),
                    "fecha": ahora.strftime("%Y-%m-%d"),
                    "hora": ahora.strftime("%H:%M"),
                    "dia_semana": ahora.weekday(),
                    "es_fin_semana": 1 if ahora.weekday() >= 5 else 0,
                    "es_quincena": 1 if ahora.day in [14, 15, 16, 29, 30, 31, 1] else 0,
                    "nodo_id": nodo["id"],
                    "nodo_nombre": nodo["nombre"],
                    "lat": nodo["lat"],
                    "lon": nodo["lon"],
                    "velocidad_actual_kmh": vel_actual,
                    "velocidad_libre_kmh": vel_libre,
                    "tiempo_actual_seg": t_actual,
                    "tiempo_libre_seg": t_libre,
                    "ratio_velocidad": ratio,
                    "confianza_dato": confianza,
                    "temp_c": clima["temp_c"],
                    "precipitacion_mm": clima["precipitacion_mm"],
                    "codigo_clima": clima["codigo_clima"],
                    "nivel_congestion": clase
                })
            except Exception as e:
                print(f"Error en {nodo['id']}: {e}")

if __name__ == "__main__":
    main()
