import requests
import json

print("--- Starting Apple App Store Feasibility Test (Official API) ---")

app_id = "324684580"  # Spotify's ID
# Official Apple RSS Feed endpoint for reviews
url = f"https://itunes.apple.com/us/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"

try:
    print(f"Fetching recent reviews from official Apple API for ID: {app_id}...")
    
    # We can use basic headers here since it's a public API
    headers = {"User-Agent": "Sciencia-Data-Pipeline-Test/1.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # The JSON has a 'feed' containing an 'entry' list
        entries = data.get('feed', {}).get('entry', [])
        
        # The first entry in Apple's feed is often metadata about the app, not a review
        reviews = [entry for entry in entries if 'author' in entry]
        
        print(f"\nSUCCESS: Fetched {len(reviews)} reviews seamlessly.")
        
        if reviews:
            print("\n--- Sample Metadata Check (First Review) ---")
            sample = reviews[0]
            
            # Extracting the metadata from Apple's specific JSON structure
            date = sample.get('updated', {}).get('label')
            rating = sample.get('im:rating', {}).get('label')
            title = sample.get('title', {}).get('label')
            text = sample.get('content', {}).get('label')
            
            print(f"Date Posted:  {date}")
            print(f"Star Rating:  {rating} Stars")
            print(f"Review Title: {title}")
            print(f"Review Text:  {text[:100]}...")
            
    else:
        print(f"\nFAILED: Received HTTP {response.status_code}")
        print(response.text) # Print the error if it fails
        
except Exception as e:
    print(f"\nFAILED: A script error occurred - {e}")

print("\nFeasibility test complete.")