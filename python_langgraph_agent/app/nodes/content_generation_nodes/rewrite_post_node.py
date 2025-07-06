from typing import Dict, Any
from ...state import GeneratePostState # Corrected relative import
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
import os

async def rewrite_post_node(state: GeneratePostState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rewrites a post using an LLM based on user feedback.
    """
    user_feedback = state.userResponse
    current_post = state.post

    print(f"DEBUG: Node: rewrite_post_node. User feedback: '{user_feedback}'. Current post: '{current_post[:100]}...'")

    if not user_feedback:
        print("DEBUG: No user feedback provided for rewrite. Returning current post.")
        return {"post": current_post, "userResponse": None, "complexPost": None, "condenseCount": 0}

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found for rewrite_post_node.")
        return {"post": current_post, "userResponse": None, "complexPost": None, "condenseCount": 0, "error": "LLM API key not configured."}

    try:
        llm = ChatAnthropic(model="claude-3-haiku-20240307", api_key=api_key, temperature=0.5)

        prompt_text = (
            f"Please rewrite the following social media post based on the provided user feedback. "
            f"Aim to incorporate the feedback effectively while maintaining clarity and engagement. "
            f"Try to keep the length suitable for social media (e.g., around 200-280 characters).\n\n"
            f"Original Post:\n\"\"\"\n{current_post}\n\"\"\"\n\n"
            f"User Feedback:\n\"\"\"\n{user_feedback}\n\"\"\"\n\n"
            f"Rewritten Post:\n"
        )

        messages = [HumanMessage(content=prompt_text)]

        print(f"DEBUG: Calling LLM to rewrite post with feedback: '{user_feedback}'")
        response = await llm.ainvoke(messages)
        rewritten_post_content = response.content.strip()

        print(f"DEBUG: LLM rewritten post: {rewritten_post_content}")
        # Reset userResponse, complexPost, and condenseCount as it's a new version of the post
        return {"post": rewritten_post_content, "userResponse": None, "complexPost": None, "condenseCount": 0}

    except Exception as e:
        print(f"ERROR: LLM call failed in rewrite_post_node: {e}")
        # Return original post but clear feedback to avoid loop if error persists
        return {"post": current_post, "userResponse": None, "complexPost": None, "condenseCount": 0, "error": f"Error during rewrite: {str(e)}"}
