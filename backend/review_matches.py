import requests
from app.config import settings

API_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": f"Bearer {settings.devmind_api_key}"}

def get_matches():
    response = requests.get(f"{API_URL}/career/matches", headers=HEADERS)
    response.raise_for_status()
    return response.json()["matches"]

def review_all_matches():
    matches = get_matches()

    if not matches:
        print("No pending matches to review.")
        return
    
    print(f"\n Found {len(matches)} job matches to review.\n")
    
    for i , match in enumerate(matches, 1):
        print(f"--- Match {i}/{len(matches)} ---")
        print(f"Title:    {match['title']}")
        print(f"Company:  {match['company']}")
        print(f"Location: {match['location']}")
        print(f"Fit:      {match['fit_score']}")
        print(f"Reason:   {match['fit_reason']}")
        print(f"Apply at: {match['url']}")
        
        
        
        answer = input("\nDo you want to pursue this job? (y/n/skip): ").strip().lower()
        
        if answer =="y":
            requests.post(f"{API_URL}/career/matches/{match['id']}/prepare", headers=HEADERS)
            print(">> Marked as interested. Go apply at the URL above, then come back and confirm.\n")
        elif answer == "n":
            requests.post(f"{API_URL}/career/matches/{match['id']}/reject",headers=HEADERS)
            print(">> Rejected. This won't show up again.\n")
        else:
            print(">> Skipped for now.\n")

            


if __name__ == "__main__":
    review_all_matches()