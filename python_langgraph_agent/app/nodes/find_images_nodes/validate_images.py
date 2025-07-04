from typing import Dict, Any, List
from ...state import GeneratePostState # Corrected relative import

async def validate_images_node(state: GeneratePostState, config: Dict[str, Any]) -> Dict[str, Any]: # Added config
    """
    Placeholder for validating image URLs from 'imageOptions'.
    Filters out invalid or unwanted images.
    """
    print(f"DEBUG: Validating images. Options received: {state.imageOptions}")

    validated_options: List[str] = []
    if state.imageOptions:
        for img_url in state.imageOptions:
            # Mock validation:
            # - Keep .jpg and .png
            # - Ensure it's https
            # - Not a blacklisted domain (example)
            if not img_url.lower().startswith("https://"):
                print(f"DEBUG: Invalidating image (not https): {img_url}")
                continue
            if "example-blacklisted.com" in img_url:
                print(f"DEBUG: Invalidating image (blacklisted domain): {img_url}")
                continue
            if not (img_url.lower().endswith(".jpg") or img_url.lower().endswith(".png")):
                print(f"DEBUG: Invalidating image (unsupported extension): {img_url}")
                continue
            validated_options.append(img_url)

    print(f"DEBUG: validate_images_node validated options: {validated_options}")
    # This will overwrite the existing imageOptions with the validated list.
    return {"imageOptions": validated_options}
