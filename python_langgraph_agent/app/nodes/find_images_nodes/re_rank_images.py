from typing import Dict, Any, Optional
from ...state import GeneratePostState # Corrected relative import
from ...models import ImageModel # Corrected import for ImageModel

async def re_rank_images_node(state: GeneratePostState, config: Dict[str, Any]) -> Dict[str, Any]: # Added config
    """
    Placeholder for re-ranking validated images and selecting the best one.
    Sets the 'image' field in the state.
    Uses 'report' and 'post' content for context if available.
    """
    print(f"DEBUG: Re-ranking images. Validated options: {state.imageOptions}")
    print(f"DEBUG: Context - Report: '{state.report[:100]}...', Post: '{state.post[:100]}...'")

    selected_image: Optional[ImageModel] = None

    if state.imageOptions:
        # Mock re-ranking logic:
        # - Prefer .png over .jpg if both exist.
        # - Or just pick the first one.
        # A real implementation would use more sophisticated logic, possibly an LLM or image analysis.

        preferred_url = None
        for img_url in state.imageOptions:
            if img_url.lower().endswith(".png"):
                preferred_url = img_url
                break

        if not preferred_url and state.imageOptions:
            preferred_url = state.imageOptions[0] # Pick the first valid one

        if preferred_url:
            # Mock mime type, a real validator would determine this
            mime_type = "image/png" if preferred_url.lower().endswith(".png") else "image/jpeg"
            selected_image = ImageModel(imageUrl=preferred_url, mimeType=mime_type)
            print(f"DEBUG: re_rank_images_node selected image: {selected_image}")
        else:
            print("DEBUG: re_rank_images_node: No suitable image found after re-ranking.")
    else:
        print("DEBUG: re_rank_images_node: No image options to re-rank.")

    return {"image": selected_image} # Updates the 'image' field in GeneratePostState
