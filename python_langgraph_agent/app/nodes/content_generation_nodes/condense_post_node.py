from typing import Dict, Any
from ...state import GeneratePostState # Corrected relative import

async def condense_post_node(state: GeneratePostState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for the node that condenses a post if it's too long.
    Original: src/agents/generate-post/nodes/condense-post.ts
    """
    print(f"DEBUG: Node: condense_post_node. Current post length: {len(state.post)}. Condense count: {state.condenseCount}")

    current_post = state.post
    new_condense_count = state.condenseCount + 1

    if len(current_post) > 280: # Target length, e.g., for Twitter
        # Mock LLM call to condense the post
        # Remove last few words, add ellipsis
        words = current_post.split()
        condensed_post = " ".join(words[:-5]) + "..." if len(words) > 10 else current_post[:277] + "..."
        if len(condensed_post) > 280:
            condensed_post = condensed_post[:277] + "..."

        print(f"DEBUG: Condensed post (attempt {new_condense_count}): {condensed_post}")
        return {"post": condensed_post, "condenseCount": new_condense_count}
    else:
        print("DEBUG: Post is already within length limits, no condensation needed.")
        # Return current post and count, no change to post itself
        return {"post": current_post, "condenseCount": state.condenseCount}
