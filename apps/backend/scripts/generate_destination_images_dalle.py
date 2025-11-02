"""Generate destination images using DALL-E 3.

This script generates beautiful, destination-specific images showing iconic landmarks.
"""

import os
import sys
import time
import urllib.request
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

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

def get_destination_prompt(destination: str) -> str:
    """Generate a DALL-E prompt for each destination showing iconic landmarks."""
    prompts = {
        "Thailand": "Beautiful scenic photo of Bangkok's Grand Palace with golden spires and ornate architecture, vibrant blue sky, travel photography style",
        "Malaysia": "Stunning photo of Petronas Twin Towers in Kuala Lumpur at golden hour, modern cityscape, professional travel photography",
        "Indonesia": "Scenic photo of Bali's iconic Pura Ulun Danu Bratan water temple with Mount Bratan in background, serene lake reflection, travel photography",
        "Philippines": "Beautiful tropical beach in Palawan with crystal clear turquoise water, limestone cliffs, El Nido, paradise island scenery",
        "Vietnam": "Stunning photo of Halong Bay with limestone karsts rising from emerald waters, traditional junk boat, dramatic landscape",
        "Cambodia": "Majestic Angkor Wat temple at sunrise with palm trees, ancient stone temples, golden hour lighting, travel photography",
        "Myanmar": "Scenic photo of thousands of ancient Bagan temples at sunset, hot air balloons floating, golden pagodas, magical atmosphere",
        "Laos": "Beautiful photo of Kuang Si Falls with turquoise blue pools, lush green jungle, cascading waterfalls, tropical paradise",
        "Brunei": "Stunning photo of Sultan Omar Ali Saifuddien Mosque with golden dome reflected in water, beautiful Islamic architecture",
        "Japan": "Iconic photo of Mount Fuji with cherry blossoms in foreground, pagoda, spring season, classic Japanese landscape",
        "South Korea": "Beautiful photo of Gyeongbokgung Palace in Seoul with traditional Korean architecture, mountains in background, vibrant colors",
        "China": "Majestic Great Wall of China winding through mountains, watchtowers, dramatic landscape, golden hour lighting",
        "Hong Kong": "Stunning cityscape of Hong Kong Victoria Harbour at night, illuminated skyscrapers, harbor lights reflected in water",
        "Taiwan": "Photo of Taipei 101 tower at night with city lights, modern architecture, urban skyline, dramatic blue hour",
        "India": "Majestic Taj Mahal at sunrise with reflection pool, marble architecture, golden light, iconic monument",
        "Australia": "Stunning photo of Sydney Opera House and Harbour Bridge at sunset, harbor waters, iconic Australian landmarks",
        "New Zealand": "Breathtaking Milford Sound with dramatic mountain peaks, waterfalls, fjord landscape, pristine nature",
        "Sri Lanka": "Scenic photo of Sigiriya Rock Fortress rising from jungle, ancient ruins on top, dramatic landscape",
        "Macau": "Stunning photo of Ruins of St. Paul's facade with grand staircase, historic Portuguese architecture in Macau",
        "United States": "Iconic New York City skyline with Statue of Liberty, Manhattan skyscrapers, sunset over Hudson River",
        "United Kingdom": "Classic photo of London with Big Ben, Tower Bridge over Thames River, red double-decker bus, iconic British scene",
        "France": "Beautiful photo of Eiffel Tower in Paris at golden hour with Champ de Mars gardens, classic French landmark",
        "Germany": "Fairytale Neuschwanstein Castle in Bavaria surrounded by Alps mountains, autumn colors, romantic architecture",
        "Italy": "Stunning photo of Rome Colosseum at sunset, ancient Roman architecture, golden light, historic landmark",
        "Spain": "Beautiful photo of Sagrada Familia in Barcelona, Gaudi's ornate architecture, blue sky, iconic Spanish landmark",
        "Switzerland": "Majestic Matterhorn mountain peak reflected in alpine lake, Swiss Alps, snow-capped peaks, pristine nature",
        "Netherlands": "Scenic photo of Amsterdam canals with traditional Dutch houses, bicycles, bridges, colorful buildings",
        "Greece": "Stunning photo of Santorini with white-washed buildings, blue domes, overlooking Aegean Sea, golden hour",
        "Turkey": "Beautiful photo of Istanbul with Blue Mosque and Hagia Sophia, Bosphorus strait, sunset skyline",
        "United Arab Emirates": "Stunning photo of Burj Khalifa tower in Dubai at night, modern architecture, city lights, luxurious skyline",
        "Singapore": "Iconic photo of Marina Bay Sands with waterfront, Gardens by the Bay supertrees, modern Singapore skyline at blue hour",
    }
    return prompts.get(destination, f"Beautiful scenic photo of iconic landmark in {destination}, travel photography style, professional quality")

def generate_and_download_image(destination: str, output_dir: Path, client: OpenAI):
    """Generate an image using DALL-E 3 and download it."""
    sanitized = sanitize_destination_name(destination)
    output_path = output_dir / f"{sanitized}.jpg"
    
    if output_path.exists():
        print(f"✓ {destination} - already exists")
        return True
    
    prompt = get_destination_prompt(destination)
    
    try:
        print(f"🎨 Generating image for {destination}...")
        print(f"   Prompt: {prompt[:80]}...")
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",  # Wide landscape format
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # Download the generated image
        print(f"⬇️  Downloading {destination}...")
        with urllib.request.urlopen(image_url, timeout=60) as response:
            image_data = response.read()
            
        with open(output_path, 'wb') as f:
            f.write(image_data)
            
        print(f"✅ {destination} - saved as {sanitized}.jpg\n")
        
        # Rate limiting - DALL-E 3 has rate limits
        time.sleep(2)
        return True
        
    except Exception as e:
        print(f"❌ {destination} - Error: {e}\n")
        return False

def main():
    api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    # Output directory
    script_dir = Path(__file__).parent
    frontend_dir = script_dir.parent.parent / "frontend" / "public" / "destination-images"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("🎨 DALL-E 3 Destination Image Generator")
    print("=" * 70)
    print(f"📁 Output directory: {frontend_dir}")
    print(f"🖼️  Generating {len(DESTINATIONS)} destination images...")
    print(f"⏱️  Estimated time: ~{len(DESTINATIONS) * 10 // 60} minutes")
    print("=" * 70)
    print()
    
    success_count = 0
    failed = []
    
    for idx, destination in enumerate(DESTINATIONS, 1):
        print(f"[{idx}/{len(DESTINATIONS)}] ", end="")
        if generate_and_download_image(destination, frontend_dir, client):
            success_count += 1
        else:
            failed.append(destination)
    
    print("\n" + "=" * 70)
    print(f"✨ Done! Generated {success_count}/{len(DESTINATIONS)} images")
    if failed:
        print(f"❌ Failed: {', '.join(failed)}")
    print("=" * 70)

if __name__ == "__main__":
    main()

