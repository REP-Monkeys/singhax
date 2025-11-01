# Pre-generate Destination Images

This script generates destination images for common travel destinations and saves them to the frontend public directory for immediate use.

## Why Pre-generate?

- **Instant loading**: Images load immediately from static files
- **No rate limits**: Avoid OpenAI rate limits during runtime
- **Better UX**: No waiting for image generation when users visit the dashboard
- **Cost efficiency**: Generate once, use many times

## How to Run

1. **Make sure you have OpenAI API key set in `.env`**:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```

2. **Activate your virtual environment**:
   ```bash
   cd apps/backend
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Run the script**:
   ```bash
   python scripts/pre_generate_destination_images.py
   ```

## What It Does

- Generates images for ~30 common destinations (ASEAN, Asia-Pacific, and popular worldwide destinations)
- Saves images to `apps/frontend/public/destination-images/`
- Uses 15-second delays between requests to avoid rate limits
- Skips destinations that already have images (safe to re-run)

## Estimated Time

- ~30 destinations × 15 seconds = ~7.5 minutes
- Plus ~10-15 seconds per image generation = ~10-12 minutes total

## Generated Destinations

### Area A (ASEAN)
- Thailand, Malaysia, Indonesia, Philippines, Vietnam, Cambodia, Myanmar, Laos, Brunei

### Area B (Asia-Pacific)
- Japan, South Korea, China, Hong Kong, Taiwan, India, Australia, New Zealand, Sri Lanka, Macau

### Popular Worldwide
- United States, United Kingdom, France, Germany, Italy, Spain, Switzerland, Netherlands, Greece, Turkey, UAE, Singapore

### Multi-destinations
- Japan, Korea
- Thailand, Malaysia

## After Running

The frontend will automatically use these pre-generated images. The dashboard will:
1. First check `/destination-images/` (public directory)
2. Fall back to API generation only if image not found in public directory

## Troubleshooting

- **Rate limit errors**: The script waits 15 seconds between requests. If you still hit limits, increase the delay in the script.
- **Missing images**: Some destinations might fail due to API errors. You can re-run the script - it will skip existing images.
- **Different destinations**: Edit `COMMON_DESTINATIONS` in the script to add/remove destinations.

