from typing import Dict, Any
from ...state import GeneratePostState # Corrected relative import
from ...models import ComplexPost # Corrected import for ComplexPost

async def rewrite_post_with_split_url_node(state: GeneratePostState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for the node that rewrites a post by splitting the URL
    into a follow-up comment/reply, based on user feedback.
    Original: src/agents/generate-post/nodes/rewrite-with-split-url.ts
    """
    user_feedback = state.userResponse # User feedback might indicate to split
    current_post = state.post

    print(f"DEBUG: Node: rewrite_post_with_split_url_node. User feedback: '{user_feedback}'. Current post: '{current_post[:100]}...'")

    # Mock logic: Assume the first link found is the one to split out.
    # A real implementation would parse the post for URLs.
    main_post_content = current_post
    reply_post_content = ""

    if state.links and len(state.links) > 0:
        url_to_split = state.links[0]
        if url_to_split in main_post_content:
            main_post_content = main_post_content.replace(url_to_split, "").strip()
            # Remove extra spaces that might result from replacement
            main_post_content = ' '.join(main_post_content.split())
            reply_post_content = f"Find out more here: {url_to_split}"
        else: # URL not in post, just make a generic reply with the URL
            reply_post_content = f"Link: {url_to_split}"
    else: # No links available in state to split out
        reply_post_content = "No primary link was found to split."

    # Ensure main post is not overly long
    if len(main_post_content) > 280:
        main_post_content = main_post_content[:277] + "..."

    complex_post_data = ComplexPost(main_post=main_post_content, reply_post=reply_post_content)

    print(f"DEBUG: Mock split post: Main='{main_post_content}', Reply='{reply_post_content}'")

    # This node updates 'complexPost' and clears 'post'.
    # It also clears userResponse and resets condenseCount.
    return {
        "post": "", # Main post is now part of complexPost
        "complexPost": complex_post_data,
        "userResponse": None,
        "condenseCount": 0
    }
