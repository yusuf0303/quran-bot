
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_REGION_NAMES = {
    "Toshkent": "Toshkent",
    "Andijon": "Andijon",
    "Farg'ona": "Farg'ona",
    "Namangan": "Namangan",
    "Samarqand": "Samarqand",
    "Buxoro": "Buxoro",
    "Navoiy": "Nurota",
    "Xorazm": "Urganch",
    "Qashqadaryo": "Qarshi",
    "Surxondaryo": "Termiz",
    "Jizzax": "Jizzax",
    "Sirdaryo": "Guliston",
    "Nukus (Qoraqalpog'iston Res)": "Nukus"
}

def get_aladhan_data(region, district=None):
    try:
        ALADHAN_CITIES = {
            "Toshkent": "Tashkent",
            "Andijon": "Andijan",
            "Farg'ona": "Fergana",
            "Namangan": "Namangan",
            "Samarqand": "Samarkand",
            "Buxoro": "Bukhara",
            "Navoiy": "Navoi",
            "Xorazm": "Urgench",
            "Qashqadaryo": "Qarshi",
            "Surxondaryo": "Termiz",
            "Jizzax": "Jizzakh",
            "Sirdaryo": "Guliston",
            "Nukus (Qoraqalpog'iston Res)": "Nukus"
        }
        
        city = district if district else region
        if city in ALADHAN_CITIES:
            city = ALADHAN_CITIES[city]
        
        url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country=Uzbekistan&method=3&school=1"
        response = requests.get(url, timeout=(5, 10))
        
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("code") == 200:
                timings = res_data["data"]["timings"]
                return timings
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

print("Testing Aladhan fallback for all regions...")
for region in API_REGION_NAMES:
    data = get_aladhan_data(region)
    if data:
        print(f"OK {region}: {data['Fajr']}")
    else:
        print(f"FAIL {region}: Failed")
