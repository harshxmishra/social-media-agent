from typing import Dict, Any
from ...state import GeneratePostState # Corrected relative import
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
import os

async def generate_post_node(state: GeneratePostState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a social media post using an LLM based on the content report.
    """
    print(f"DEBUG: Node: generate_post_node. Report: '{state.report[:100]}...'")
    if not state.report or state.report.startswith("Error:") or state.report == "No content was available to generate a report.":
        print(f"DEBUG: No valid report available to generate a post from. Report content: {state.report}")
        return {"post": "Error: Could not generate post due to missing or invalid report.", "complexPost": None, "condenseCount": 0}

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found for generate_post_node.")
        return {"post": "Error: LLM API key not configured.", "complexPost": None, "condenseCount": 0}

    try:
        llm = ChatAnthropic(model="claude-3-haiku-20240307", api_key=api_key, temperature=0.7) # Higher temp for creativity

        # Simple prompt for now. The original TS project has more complex prompt construction.
        # This prompt should ideally guide for length, tone, hashtags, and call to action.
        # Including original links for context for the LLM.
        links_str = "\n".join(state.links) if state.links else "the source"
        prompt_text = (
            f"Based on the following report, please draft an engaging social media post (e.g., for Twitter/X or LinkedIn). "
            f"The post should be concise, highlight key takeaways, and encourage engagement. "
            f"Mention that more details can be found at {links_str}.\n\n"
            f"Report:\n\"\"\"\n{state.report}\n\"\"\"\n\n"
            f"Draft Social Media Post (around 200-280 characters if possible for wide compatibility):\n"
        )

        messages = [HumanMessage(content=prompt_text)]

        print(f"DEBUG: Calling LLM for post generation. Report length: {len(state.report)}")
        response = await llm.ainvoke(messages)
        generated_post = response.content.strip()

        print(f"DEBUG: LLM generated post: {generated_post}")
        return {"post": generated_post, "complexPost": None, "condenseCount": 0}

    except Exception as e:
        print(f"ERROR: LLM call failed in generate_post_node: {e}")
        return {"post": f"Error during post generation: {str(e)}", "complexPost": None, "condenseCount": 0}
