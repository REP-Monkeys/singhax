"""Router for destination image generation and serving."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from app.services.image_generator import ImageGeneratorService

router = APIRouter(prefix="/destination-images", tags=["destination-images"])

# Initialize the image generator service
image_service = ImageGeneratorService()


@router.get("/{country}")
async def get_destination_image(country: str):
    """
    Get an existing image for a destination country.
    
    Only returns images that already exist. Does not generate new images.
    Returns 404 if the image doesn't exist.
    """
    try:
        # Only get existing image, don't generate
        image_path_relative = image_service.get_image_path_relative(country)
        
        if not image_path_relative:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found for {country}"
            )
        
        # Return the image file
        full_path = Path("apps/backend/uploads") / image_path_relative
        
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found for {country}"
            )
        
        return FileResponse(
            str(full_path),
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=31536000"  # Cache for 1 year
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image request: {str(e)}"
        )


@router.post("/generate/{country}")
async def generate_destination_image(country: str):
    """
    Force generate a new image for a destination (even if one exists).
    Useful for regenerating images.
    """
    try:
        # Remove existing image if it exists
        image_path = image_service._get_image_path(country)
        if image_path.exists():
            image_path.unlink()
        
        # Generate new image
        image_path_relative = await image_service.get_or_generate_image(country)
        
        if not image_path_relative:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not generate image for {country}. OpenAI API may not be configured."
            )
        
        return {
            "message": f"Image generated successfully for {country}",
            "path": image_path_relative
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating image: {str(e)}"
        )

