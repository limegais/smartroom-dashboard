import urllib.request
import json

url = (
    'https://api.open-meteo.com/v1/forecast'
    '?latitude=-7.5561&longitude=110.8316'
    '&current=temperature_2m,relative_humidity_2m,apparent_temperature,'
    'weather_code,wind_speed_10m,precipitation,cloud_cover,uv_index,is_day'
    '&timezone=Asia%2FJakarta'
    '&forecast_days=1'
)

print("[TEST] Menghubungi Open-Meteo API untuk UNS Surakarta...")
req = urllib.request.Request(url, headers={'User-Agent': 'SmartRoom-Test/1.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    c = data['current']
    print("[OK] BERHASIL! Data cuaca UNS Surakarta:")
    print(f"  Suhu Udara      : {c['temperature_2m']} degC")
    print(f"  Terasa Seperti  : {c['apparent_temperature']} degC")
    print(f"  Kelembaban      : {c['relative_humidity_2m']} %")
    print(f"  Kecepatan Angin : {c['wind_speed_10m']} km/h")
    print(f"  Curah Hujan     : {c['precipitation']} mm")
    print(f"  Tutupan Awan    : {c['cloud_cover']} %")
    print(f"  Indeks UV       : {c['uv_index']}")
    print(f"  Kode Cuaca (WMO): {c['weather_code']}")
    print(f"  Siang Hari      : {bool(c['is_day'])}")
    print(f"  Waktu Data      : {c['time']}")
except Exception as e:
    print(f"[GAGAL] Error: {e}")
