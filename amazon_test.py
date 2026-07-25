import requests
from bs4 import BeautifulSoup
import time
import random

# 1. Define the target URL and base parameters
ASIN = "B09NBWL8J5"
base_url = f"https://www.amazon.com/product-reviews/{ASIN}/"

# 2. Set realistic headers to bypass basic blocks
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# 3. Test Pagination & Anti-Scraping Resilience
# We will try to fetch the first 3 pages.
for page in range(1, 4):
    print(f"\n--- Fetching Page {page} ---")
    
    # Add the pageNumber parameter to the URL
    url = f"{base_url}?pageNumber={page}"
    
    # Send the GET request
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"FAILED: Received HTTP {response.status_code}")
        print("This indicates Amazon's anti-bot system blocked the request.")
        break
        
    print(f"SUCCESS: Page {page} loaded (HTTP 200)")
    
    # 4. Parse the HTML and extract Metadata
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find all review containers on the page
    reviews = soup.select('div[data-hook="review"]')
    
    if not reviews:
        print("No reviews found on page. Amazon might be serving a CAPTCHA.")
        break
        
    print(f"Found {len(reviews)} reviews on Page {page}.")
    
    # Extract data from the very first review on the page as a test
    first_review = reviews[0]
    
    try:
        # Using standard Amazon data-hook CSS selectors
        rating = first_review.select_one('i[data-hook="review-star-rating"]').text.strip()
        date = first_review.select_one('span[data-hook="review-date"]').text.strip()
        text = first_review.select_one('span[data-hook="review-body"]').text.strip()
        
        print(f"Sample Rating: {rating}")
        print(f"Sample Date: {date}")
        print(f"Sample Text Extract: {text[:50]}...")
        
    except AttributeError:
        print("Failed to extract metadata. The HTML structure may have changed.")
        
    # 5. Respect rate limits with a random delay before the next page
    delay = random.uniform(2.5, 4.5)
    print(f"Sleeping for {delay:.2f} seconds...")
    time.sleep(delay)

print("\nFeasibility test complete.")