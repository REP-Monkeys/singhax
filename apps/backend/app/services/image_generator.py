"""Service for generating destination images using OpenAI DALL-E."""

import os
import httpx
import asyncio
from pathlib import Path
from typing import Optional
from openai import OpenAI
from app.core.config import settings


class ImageGeneratorService:
    """Service for generating and caching destination images."""
    
    def __init__(self):
        self.openai_client = None
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        
        # Create images directory if it doesn't exist
        self.images_dir = Path("apps/backend/uploads/destination_images")
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def _sanitize_country_name(self, country: str) -> str:
        """Sanitize country name for use in filenames."""
        # Remove special characters and replace spaces with underscores
        sanitized = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in country)
        return sanitized.replace(' ', '_').lower()
    
    def _get_image_path(self, country: str) -> Path:
        """Get the file path for a country's image."""
        sanitized = self._sanitize_country_name(country)
        return self.images_dir / f"{sanitized}.png"
    
    def _generate_prompt(self, country: str) -> str:
        """Generate a prompt for DALL-E image generation."""
        return (
            f"Beautiful, scenic travel destination image of {country}. "
            f"Show iconic landmarks, landscapes, or cityscapes that represent {country}. "
            f"Professional travel photography style, vibrant colors, wide aspect ratio suitable for a travel card. "
            f"No text or people in the image."
        )
    
    async def get_or_generate_image(self, country: str) -> Optional[str]:
        """
        Get existing image or generate a new one for a country.
        
        Args:
            country: Name of the country/destination
            
        Returns:
            Path to the image file (relative to uploads directory) or None if generation fails
        """
        if not self.openai_client:
            print(f"⚠️  OpenAI API key not configured, cannot generate image for {country}")
            return None
        
        image_path = self._get_image_path(country)
        
        # Return existing image if it exists
        if image_path.exists():
            print(f"✓ Using existing image for {country}")
            return f"destination_images/{image_path.name}"
        
        # Generate new image
        try:
            print(f"🎨 Generating image for {country}...")
            prompt = self._generate_prompt(country)
            
            # Call DALL-E API (run in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.openai_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",  # Square format, we'll crop if needed
                    quality="standard",
                    n=1,
                )
            )
            
            image_url = response.data[0].url
            
            # Download the image
            async with httpx.AsyncClient() as client:
                img_response = await client.get(image_url)
                img_response.raise_for_status()
                
                # Save the image
                with open(image_path, "wb") as f:
                    f.write(img_response.content)
            
            print(f"✓ Generated and saved image for {country}")
            return f"destination_images/{image_path.name}"
            
        except Exception as e:
            print(f"❌ Failed to generate image for {country}: {str(e)}")
            return None
    
    def image_exists(self, country: str) -> bool:
        """Check if an image already exists for a country."""
        image_path = self._get_image_path(country)
        return image_path.exists()
    
    def get_image_path_relative(self, country: str) -> Optional[str]:
        """Get relative path to image if it exists."""
        image_path = self._get_image_path(country)
        if image_path.exists():
            return f"destination_images/{image_path.name}"
        return None

