"""Pre-generate destination images for common countries.

This script generates images for common travel destinations and saves them
to the frontend public directory for immediate use, avoiding runtime generation delays.
"""

import asyncio
import httpx
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables (try multiple locations)
script_dir = Path(__file__).parent
env_paths = [
    script_dir.parent.parent.parent / ".env",  # Project root
    script_dir.parent.parent / ".env",  # Backend root
    Path.home() / ".env",  # Home directory
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"📄 Loaded .env from: {env_path}")
        break

# Common destinations based on travel insurance regions
COMMON_DESTINATIONS = [
    # Area A: ASEAN (most common for Singapore travelers)
    "Thailand",
    "Malaysia",
    "Indonesia",
    "Philippines",
    "Vietnam",
    "Cambodia",
    "Myanmar",
    "Laos",
    "Brunei",
    
    # Area B: Asia-Pacific (very common)
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
    
    # Popular worldwide destinations
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
    "Singapore",  # Home country, but useful to have
]

# Also handle multi-destination cases
MULTI_DESTINATIONS = [
    "Japan, Korea",
    "Thailand, Malaysia",
]


def sanitize_country_name(country: str) -> str:
    """Sanitize country name for use in filenames."""
    sanitized = "".join(c if c.isalnum() or c in (' ', '-', '_', ',') else '' for c in country)
    return sanitized.replace(' ', '_').replace(',', '_').lower()


def generate_prompt(country: str) -> str:
    """Generate a prompt for DALL-E image generation."""
    return (
        f"Beautiful, scenic travel destination image of {country}. "
        f"Show iconic landmarks, landscapes, or cityscapes that represent {country}. "
        f"Professional travel photography style, vibrant colors, wide aspect ratio suitable for a travel card. "
        f"No text or people in the image."
    )


async def generate_and_save_image(
    client: OpenAI,
    destination: str,
    output_dir: Path,
    delay_seconds: int = 60,
    max_retries: int = 3
) -> bool:
    """Generate an image for a destination and save it.
    
    Args:
        client: OpenAI client
        destination: Destination name
        output_dir: Directory to save images
        delay_seconds: Delay between requests (default 60 seconds = 1 per minute)
        max_retries: Maximum number of retries on rate limit errors
        
    Returns:
        True if successful, False otherwise
    """
    sanitized = sanitize_country_name(destination)
    image_path = output_dir / f"{sanitized}.png"
    
    # Skip if already exists
    if image_path.exists():
        print(f"⏭️  Skipping {destination} - image already exists")
        return True
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                wait_time = 65  # Wait a bit more than 60 seconds to ensure window reset
                print(f"🔄 Retry attempt {attempt + 1}/{max_retries} - waiting {wait_time} seconds for rate limit reset...")
                await asyncio.sleep(wait_time)
            
            print(f"🎨 Generating image for {destination}...")
            prompt = generate_prompt(destination)
            
            # Call DALL-E API (run in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
            )
            
            image_url = response.data[0].url
            
            # Download the image
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                img_response = await http_client.get(image_url)
                img_response.raise_for_status()
                
                # Save the image
                with open(image_path, "wb") as f:
                    f.write(img_response.content)
            
            print(f"✅ Generated and saved image for {destination}")
            
            # Wait before next request to avoid rate limits
            if delay_seconds > 0:
                print(f"⏳ Waiting {delay_seconds} seconds before next request...")
                await asyncio.sleep(delay_seconds)
            
            return True
            
        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in str(e):
                if attempt < max_retries - 1:
                    print(f"⚠️  Rate limit exceeded. Your account allows 1 image per minute.")
                    print(f"   This means you've generated an image recently (within the last minute).")
                    print(f"   Waiting for rate limit window to reset...")
                    # Don't return False yet, will retry in next iteration
                    continue
                else:
                    print(f"❌ Rate limit hit after {max_retries} attempts. Please wait a full minute and try again.")
                    return False
            else:
                print(f"❌ Failed to generate image for {destination}: {str(e)}")
                return False
    
    return False


async def main():
    """Main function to generate all destination images."""
    # Get OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("   Please set it in your .env file")
        sys.exit(1)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Setup output directory (frontend public/src directory)
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "apps" / "frontend" / "public" / "src"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Saving images to: {output_dir}")
    print(f"📋 Generating images for {len(COMMON_DESTINATIONS) + len(MULTI_DESTINATIONS)} destinations")
    print(f"⏱️  Estimated time: ~{(len(COMMON_DESTINATIONS) + len(MULTI_DESTINATIONS)) * 60 / 60:.1f} minutes (1 image per minute)")
    print()
    
    # Generate images for single destinations
    all_destinations = COMMON_DESTINATIONS + MULTI_DESTINATIONS
    success_count = 0
    fail_count = 0
    
    for i, destination in enumerate(all_destinations, 1):
        print(f"[{i}/{len(all_destinations)}] Processing {destination}...")
        
        # Always wait 60 seconds between requests (1 per minute rate limit)
        # This ensures we never hit the rate limit, even if we've made requests recently
        delay = 60
        
        success = await generate_and_save_image(
            client,
            destination,
            output_dir,
            delay_seconds=delay
        )
        
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        print()  # Blank line for readability
    
    # Summary
    print("=" * 60)
    print(f"✅ Successfully generated: {success_count} images")
    if fail_count > 0:
        print(f"❌ Failed: {fail_count} images")
    print(f"📁 Images saved to: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

