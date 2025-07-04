from typing import Dict, Any
from ...state import GeneratePostState # Corrected relative import

async def generate_post_node(state: GeneratePostState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for the node that generates the social media post.
    Original: src/agents/generate-post/nodes/generate-post/index.ts

    This node uses the 'report' and other context to generate a draft post.
    """
    print(f"DEBUG: Node: generate_post_node. Report: '{state.report[:100]}...'")
    if not state.report:
        print("DEBUG: No report available to generate a post from.")
        # Potentially return an error or a specific state indicating failure
        return {"post": "Error: Could not generate post due to missing report."}

    # Mock LLM call to generate a post from the report
    mock_post = f"Exciting news! Based on recent findings ({state.report[:50]}...), " \
                f"we've discovered amazing things. Check out more at {state.links[0] if state.links else 'our website'}! #Innovation #Updates"

    # Ensure post is not overly long for initial generation, though condenseNode will handle it
    if len(mock_post) > 300: # Arbitrary limit for mock
        mock_post = mock_post[:297] + "..."

    print(f"DEBUG: Generated mock post: {mock_post}")
    return {"post": mock_post, "complexPost": None, "condenseCount": 0} # Reset condenseCount and complexPost here
