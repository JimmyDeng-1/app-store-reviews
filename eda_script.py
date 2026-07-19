import requests
import pandas as pd
import time

print("--- Starting Multi-App Controlled Data Collection & EDA ---")

# Target Apps (App Store IDs)
apps = {
    "Spotify": "324684580",
    "Netflix": "363590051",
    "TikTok": "835599320",
    "Instagram": "389801252",
    "YouTube": "544007664"
}

# Target Storefronts (Country Codes)
countries = ["us", "gb", "ca", "au", "in"]

all_reviews = []

print(f"Targeting {len(apps)} apps across {len(countries)} storefronts...")
print("Goal: Collect up to 500 reviews per app/country combination.\n")

for app_name, app_id in apps.items():
    for country in countries:
        print(f"Fetching {app_name} ({country.upper()})...", end=" ", flush=True)
        country_review_count = 0
        
        # Apple's API allows pagination from page 1 to 10 (max 500 reviews)
        for page in range(1, 11):
            url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"
            
            try:
                headers = {"User-Agent": "Sciencia-Data-Pipeline-EDA/1.0"}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    entries = data.get('feed', {}).get('entry', [])
                    
                    for entry in entries:
                        if 'author' in entry: # Skips the app description entry
                            review_data = {
                                'app_name': app_name,
                                'app_id': app_id,
                                'storefront': country.upper(),
                                'review_id': entry.get('id', {}).get('label'),
                                'date': entry.get('updated', {}).get('label'),
                                'rating': int(entry.get('im:rating', {}).get('label', 0)),
                                'title': entry.get('title', {}).get('label', ''),
                                'review_text': entry.get('content', {}).get('label', '')
                            }
                            all_reviews.append(review_data)
                            country_review_count += 1
                else:
                    break # Stop pagination if storefront doesn't have more pages
            except Exception as e:
                break
            
            time.sleep(0.3) # Polite rate limiting to avoid connection drops
            
        print(f"Collected {country_review_count}")

# ----------------- EDA Phase -----------------
print("\n--- Exploratory Data Analysis (EDA) Results ---")

df = pd.DataFrame(all_reviews)

if not df.empty:
    df['review_length'] = df['review_text'].apply(len)
    
    print(f"Total Reviews Collected: {len(df)}")
    
    print("\n1. Total Reviews by App:")
    print(df['app_name'].value_counts().to_string())
    
    print("\n2. Total Reviews by Storefront:")
    print(df['storefront'].value_counts().to_string())
    
    print("\n3. Rating Distribution:")
    print(df['rating'].value_counts().sort_index().to_string())
    
    print("\n4. Review Text Length:")
    print(f"   Average: {df['review_length'].mean():.1f} characters")
    print(f"   Max: {df['review_length'].max()} characters")
    
    print("\n5. Timestamp Coverage:")
    print(f"   Oldest Review: {df['date'].min()}")
    print(f"   Newest Review: {df['date'].max()}")
    
    print("\n6. Duplicate Reviews (by Review ID):")
    duplicates = df.duplicated(subset=['review_id']).sum()
    print(f"   {duplicates} duplicates found")
    
    print("\n7. Missing Fields:")
    print(df.isnull().sum().to_string())
    
    # Save to CSV for GitHub documentation
    df.to_csv('app_store_eda_sample.csv', index=False)
    print("\nDataset saved to 'app_store_eda_sample.csv' for GitHub documentation.")
else:
    print("Failed to collect data. Please check network connection.")