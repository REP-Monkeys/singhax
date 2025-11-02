"""Download destination images for travel cards.

This script downloads real destination images from Pexels API.
"""

import urllib.request
import json
import os
from pathlib import Path
import time
import sys

# Common destinations
DESTINATIONS = [
    # Area A: ASEAN
    "Thailand",
    "Malaysia",
    "Indonesia",
    "Philippines",
    "Vietnam",
    "Cambodia",
    "Myanmar",
    "Laos",
    "Brunei",
    
    # Area B: Asia-Pacific
    "Japan",
    "South Korea",
    "China",
    "Hong Kong",
    "Taiwan",
    "India",
    "Australia",
    "New Zealand",
    "Sri Lanka",
    "Macau",
    
    # Popular worldwide
    "United States",
    "United Kingdom",
    "France",
    "Germany",
    "Italy",
    "Spain",
    "Switzerland",
    "Netherlands",
    "Greece",
    "Turkey",
    "United Arab Emirates",
    "Singapore",
]

def sanitize_destination_name(destination: str) -> str:
    """Sanitize destination name to match frontend logic."""
    return destination.lower().replace(' ', '_').replace(',', '_')

def get_destination_search_query(destination: str) -> str:
    """Get the best search query for a destination."""
    # Map destinations to iconic landmarks or views
    landmark_map = {
        "Thailand": "bangkok grand palace temple",
        "Malaysia": "petronas towers kuala lumpur",
        "Indonesia": "bali temple rice terraces",
        "Philippines": "palawan island beach",
        "Vietnam": "halong bay vietnam",
        "Cambodia": "angkor wat temple",
        "Myanmar": "bagan temples myanmar",
        "Laos": "luang prabang laos",
        "Brunei": "omar ali saifuddien mosque brunei",
        "Japan": "mount fuji tokyo skyline",
        "South Korea": "seoul tower gyeongbokgung palace",
        "China": "great wall china forbidden city",
        "Hong Kong": "hong kong victoria harbour skyline",
        "Taiwan": "taipei 101 night",
        "India": "taj mahal india",
        "Australia": "sydney opera house harbour",
        "New Zealand": "milford sound new zealand mountains",
        "Sri Lanka": "sigiriya rock sri lanka",
        "Macau": "macau casino skyline",
        "United States": "new york city skyline statue liberty",
        "United Kingdom": "london big ben tower bridge",
        "France": "eiffel tower paris",
        "Germany": "neuschwanstein castle germany",
        "Italy": "colosseum rome venice",
        "Spain": "sagrada familia barcelona",
        "Switzerland": "matterhorn swiss alps",
        "Netherlands": "amsterdam canals windmills",
        "Greece": "santorini white buildings blue domes",
        "Turkey": "istanbul hagia sophia bosphorus",
        "United Arab Emirates": "burj khalifa dubai",
        "Singapore": "marina bay sands singapore",
    }
    return landmark_map.get(destination, f"{destination} landmark travel")

def download_destination_image(destination: str, output_dir: Path, api_key: str = None):
    """Download a real image for a destination using Pexels API."""
    sanitized = sanitize_destination_name(destination)
    output_path = output_dir / f"{sanitized}.jpg"
    
    if output_path.exists():
        print(f"✓ {destination} - already exists")
        return True
    
    search_query = get_destination_search_query(destination)
    
    try:
        print(f"⬇️  Searching for {destination} ({search_query})...")
        
        if api_key:
            # Use Pexels API
            headers = {
                'Authorization': api_key,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            search_url = f"https://api.pexels.com/v1/search?query={search_query.replace(' ', '+')}&per_page=1&orientation=landscape"
            req = urllib.request.Request(search_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
                
            if data.get('photos') and len(data['photos']) > 0:
                photo = data['photos'][0]
                image_url = photo['src']['large2x']  # 1920x1280
                
                # Download the actual image
                req = urllib.request.Request(image_url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    image_data = response.read()
                    
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                    
                print(f"✅ {destination} - saved as {sanitized}.jpg")
                time.sleep(1)  # Be nice to the API
                return True
            else:
                print(f"⚠️  {destination} - No images found")
                return False
        else:
            print(f"⚠️  {destination} - No API key provided, skipping")
            return False
            
    except Exception as e:
        print(f"❌ {destination} - Error: {e}")
        return False

def main():
    # Get Pexels API key from environment
    api_key = os.environ.get('PEXELS_API_KEY')
    
    if not api_key:
        print("❌ Error: PEXELS_API_KEY environment variable not set")
        print("\n📝 To get a free Pexels API key:")
        print("   1. Go to https://www.pexels.com/api/")
        print("   2. Sign up for a free account")
        print("   3. Generate an API key")
        print("   4. Set environment variable: export PEXELS_API_KEY='your-key'")
        print("\n💡 Alternatively, you can add it to your .env file")
        sys.exit(1)
    
    # Determine output directory (frontend public folder)
    script_dir = Path(__file__).parent
    frontend_dir = script_dir.parent.parent / "frontend" / "public" / "destination-images"
    
    # Create directory if it doesn't exist
    frontend_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {frontend_dir}")
    print(f"📥 Downloading REAL images for {len(DESTINATIONS)} destinations...\n")
    
    success_count = 0
    for destination in DESTINATIONS:
        if download_destination_image(destination, frontend_dir, api_key):
            success_count += 1
    
    print(f"\n✨ Done! Downloaded {success_count}/{len(DESTINATIONS)} images to {frontend_dir}")

if __name__ == "__main__":
    main()

