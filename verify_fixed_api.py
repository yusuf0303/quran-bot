
import sys
import os

# Add the current directory to sys.path to allow imports
sys.path.append(os.getcwd())

from namoz_vaqtlari.time_namoz import get_data
from namoz_vaqtlari.get_regeions import API_REGION_NAMES

print("Verifying fixed API logic for all regions...")
success_count = 0
for region in API_REGION_NAMES:
    try:
        data = get_data(region)
        if data and 'times' in data:
            print(f"OK {region}: {data['times']['tong_saharlik']}")
            success_count += 1
        else:
            print(f"FAIL {region}: No data returned")
    except Exception as e:
        print(f"ERROR {region}: {e}")

print(f"\nSummary: {success_count}/{len(API_REGION_NAMES)} regions successful.")
if success_count == len(API_REGION_NAMES):
    print("ALL REGIONS PASSED! ✅")
else:
    print("SOME REGIONS FAILED. ❌")
