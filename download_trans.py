import requests
import json
import os

URL = "https://api.alquran.cloud/v1/quran/uz.sodik"

def download():
    print(f"Downloading translation from {URL}...")
    try:
        response = requests.get(URL, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        with open("quran_trans_uz.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("Successfully downloaded and saved quran_trans_uz.json")
    except Exception as e:
        print(f"Error downloading translation: {e}")

if __name__ == "__main__":
    download()
