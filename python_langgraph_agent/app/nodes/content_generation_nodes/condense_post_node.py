from typing import Dict, Any
from ...state import GeneratePostState # Corrected relative import
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
import os

# From generate_post_flow.py, ensure consistency
MAX_CONDENSE_ATTEMPTS = 3
TARGET_POST_LENGTH = 280 # e.g., for Twitter

async def condense_post_node(state: GeneratePostState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Condenses a post using an LLM if it's too long and attempts are within limits.
    """
    current_post = state.post
    current_length = len(current_post)
    condense_count = state.condenseCount

    print(f"DEBUG: Node: condense_post_node. Current post length: {current_length}. Condense count: {condense_count}")

    if current_length <= TARGET_POST_LENGTH or condense_count >= MAX_CONDENSE_ATTEMPTS:
        if current_length > TARGET_POST_LENGTH:
            print(f"WARN: Post still too long ({current_length} chars) after {condense_count} condense attempts. Max attempts reached.")
        else:
            print("DEBUG: Post is within length limits or max condense attempts reached. No LLM condensation needed.")
        return {"post": current_post, "condenseCount": condense_count} # No change or stop trying

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found for condense_post_node.")
        # Return current post, increment count to prevent infinite loop if this error persists
        return {"post": current_post, "condenseCount": condense_count + 1}

    try:
        llm = ChatAnthropic(model="claude-3-haiku-20240307", api_key=api_key, temperature=0.2)

        prompt_text = (
            f"The following social media post is too long (currently {current_length} characters). "
            f"Please condense it to be approximately {TARGET_POST_LENGTH} characters or less, "
            f"while preserving the key message, tone, and any important links or hashtags. "
            f"Be concise and impactful.\n\n"
            f"Original Post:\n\"\"\"\n{current_post}\n\"\"\"\n\n"
            f"Condensed Post (target ~{TARGET_POST_LENGTH} characters):\n"
        )

        messages = [HumanMessage(content=prompt_text)]

        print(f"DEBUG: Calling LLM to condense post. Attempt {condense_count + 1}")
        response = await llm.ainvoke(messages)
        condensed_post_content = response.content.strip()

        print(f"DEBUG: LLM condensed post (length {len(condensed_post_content)}): {condensed_post_content}")
        return {"post": condensed_post_content, "condenseCount": condense_count + 1}

    except Exception as e:
        print(f"ERROR: LLM call failed in condense_post_node: {e}")
        # Return current post but increment count to ensure eventual loop termination
        return {"post": current_post, "condenseCount": condense_count + 1}
