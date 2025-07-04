from typing import List, Dict, Any, Union
from langgraph.graph import StateGraph, START, END # Removed Send
from ..state import GeneratePostState
from ..models import VerifyContentInput, VerifyRedditPostInput
from ..utils import get_url_type, UrlType

# Import placeholder verification nodes
from ..nodes.verification_nodes import (
    verify_general_content,
    verify_github_content,
    verify_luma_event,
    verify_youtube_content,
    verify_reddit_content_subgraph_placeholder,
    verify_tweet_subgraph_placeholder
)

# Define node names as constants for clarity and to avoid typos
VERIFY_YOUTUBE_NODE = "verify_youtube_content_node"
VERIFY_GENERAL_NODE = "verify_general_content_node"
VERIFY_GITHUB_NODE = "verify_github_content_node"
VERIFY_TWEET_SUBGRAPH_NODE = "verify_tweet_subgraph_node" # Placeholder
VERIFY_REDDIT_SUBGRAPH_NODE = "verify_reddit_subgraph_node" # Placeholder
VERIFY_LUMA_NODE = "verify_luma_event_node"


# This routing function is now simplified to process only the FIRST link.
# The called node will need to know to pick state.links[0].
# This is a TEMPORARY simplification to get past the `Send` issue.
# TODO: Revisit this for parallel processing of all links.
def route_first_link_type(state: GeneratePostState) -> str:
    """
    Determines the type of the FIRST link in the state and returns the
    name of the appropriate verification node or END if no links.
    The target node will need to be updated to process state.links[0]
    and the graph will need a loop if all links are to be processed by this subgraph.
    """
    if not state.links or len(state.links) == 0:
        print("DEBUG: route_first_link_type -> END (no links)")
        return END # No links to process

    first_link = state.links[0]
    url_type: UrlType = get_url_type(first_link)

    # The called node will use this first_link for its input.
    # We are not passing data via the router anymore, node must get it from state.
    # This requires nodes to be aware they are processing state.links[0]
    # or for the state to be updated with the "current_link_to_process" before calling this router.
    # For now, the nodes are written to take a specific link as input; this will need adjustment.

    # For this simplified router, we just return the node name.
    # The input to the node will be the *entire current state*.
    # The node itself must then pick the link.
    # To make this work with current node signatures (expecting specific input like VerifyContentInput),
    # we'd need an intermediate "prepare_input_for_X_node" or adapt nodes.
    # Let's make nodes take GeneratePostState for now and pick state.links[0].

    if url_type == "youtube":
        return VERIFY_YOUTUBE_NODE
    elif url_type == "github":
        return VERIFY_GITHUB_NODE
    elif url_type == "twitter":
        return VERIFY_TWEET_SUBGRAPH_NODE
    elif url_type == "reddit":
        return VERIFY_REDDIT_SUBGRAPH_NODE
    elif url_type == "luma":
        return VERIFY_LUMA_NODE
    elif url_type == "general":
        return VERIFY_GENERAL_NODE
    else:
        print(f"Warning: Unknown or unhandled URL type for first link: {first_link}. Ending verification.")
        return END


# Create the StateGraph
# The state being modified is GeneratePostState.
# Nodes will need to be adapted to take GeneratePostState and pick state.links[0]
# or we need a pre-processor node for each.
# For now, assume nodes will be adapted.
# Nodes will return dicts to update fields in GeneratePostState.
# e.g., a node returns {"pageContents": ["new content"]}, LangGraph merges this.
# For list accumulation, Pydantic models in Langchain state usually append/extend lists
# when the update value for a list field is also a list.
verify_links_workflow = StateGraph(GeneratePostState)

# Add the placeholder nodes
verify_links_workflow.add_node(VERIFY_YOUTUBE_NODE, verify_youtube_content)
verify_links_workflow.add_node(VERIFY_GENERAL_NODE, verify_general_content)
verify_links_workflow.add_node(VERIFY_GITHUB_NODE, verify_github_content)
verify_links_workflow.add_node(VERIFY_TWEET_SUBGRAPH_NODE, verify_tweet_subgraph_placeholder)
verify_links_workflow.add_node(VERIFY_REDDIT_SUBGRAPH_NODE, verify_reddit_content_subgraph_placeholder)
verify_links_workflow.add_node(VERIFY_LUMA_NODE, verify_luma_event)

# Set the entry point and routing
path_map = {
    VERIFY_YOUTUBE_NODE: VERIFY_YOUTUBE_NODE,
    VERIFY_GENERAL_NODE: VERIFY_GENERAL_NODE,
    VERIFY_GITHUB_NODE: VERIFY_GITHUB_NODE,
    VERIFY_TWEET_SUBGRAPH_NODE: VERIFY_TWEET_SUBGRAPH_NODE,
    VERIFY_REDDIT_SUBGRAPH_NODE: VERIFY_REDDIT_SUBGRAPH_NODE,
    VERIFY_LUMA_NODE: VERIFY_LUMA_NODE,
    END: END  # If route_first_link_type returns END
}
verify_links_workflow.add_conditional_edges(START, route_first_link_type, path_map)


# If route_first_link_type returns END (e.g., state.links is empty or unknown type),
# the graph will transition to END.
# All verification nodes lead to END.
verify_links_workflow.add_edge(VERIFY_YOUTUBE_NODE, END)
verify_links_workflow.add_edge(VERIFY_GENERAL_NODE, END)
verify_links_workflow.add_edge(VERIFY_GITHUB_NODE, END)
verify_links_workflow.add_edge(VERIFY_TWEET_SUBGRAPH_NODE, END)
verify_links_workflow.add_edge(VERIFY_REDDIT_SUBGRAPH_NODE, END)
verify_links_workflow.add_edge(VERIFY_LUMA_NODE, END)

# Compile the graph
verify_links_graph = verify_links_workflow.compile()
verify_links_graph.name = "Verify Links Subgraph (Processes First Link Only)"


if __name__ == '__main__':
    import asyncio
    # Ensure GeneratePostState can be imported if this is run directly for testing
    # This might require adjusting sys.path or running as a module if imports fail.
    # from ..state import GeneratePostState (if running as part of package)
    # For direct script run, you might need to add parent dirs to path.

    async def run_example():
        # This example will only work if node signatures are updated to take (state, config)
        # and process state.links[0]. The current placeholder nodes expect specific inputs.
        # This __main__ block is for conceptual testing of the graph structure.

        test_links_1 = ["https://www.youtube.com/watch?v=examplevideo"]
        initial_state_1 = GeneratePostState(links=test_links_1)

        print(f"--- Test 1: YouTube Link ---")
        print(f"Initial state: {{'links': {test_links_1}}}")
        async for event in verify_links_graph.astream(initial_state_1, {"configurable":{}}):
            print(f"Event: {event.keys()}") # Print node names that ran
            if END in event:
                final_state = event[END]
                print(f"Final pageContents: {final_state.get('pageContents')}")

        test_links_2 = ["https://example.com/some-general-article"]
        initial_state_2 = GeneratePostState(links=test_links_2)
        print(f"\n--- Test 2: General Link ---")
        print(f"Initial state: {{'links': {test_links_2}}}")
        async for event in verify_links_graph.astream(initial_state_2, {"configurable":{}}):
            print(f"Event: {event.keys()}")
            if END in event:
                final_state = event[END]
                print(f"Final pageContents: {final_state.get('pageContents')}")

        test_links_3 = [] # No links
        initial_state_3 = GeneratePostState(links=test_links_3)
        print(f"\n--- Test 3: No Links ---")
        print(f"Initial state: {{'links': {test_links_3}}}")
        async for event in verify_links_graph.astream(initial_state_3, {"configurable":{}}):
            print(f"Event: {event.keys()}")
            if END in event: # Should go directly to END
                final_state = event[END]
                print(f"Final pageContents (should be empty or initial): {final_state.get('pageContents')}")

        print("\nNOTE: For these tests to show meaningful output beyond routing, " +
              "the placeholder verification nodes must be updated to accept " +
              "(state: GeneratePostState, config) and extract state.links[0] for processing.")

    try:
        asyncio.run(run_example())
    except ImportError:
        print("\nERROR: Running this __main__ block directly might cause ImportErrors.")
        print("Ensure you run it as a module or adjust PYTHONPATH if needed, e.g.:")
        print("cd /app/python_langgraph_agent && poetry run python -m app.subgraphs.verify_links_graph")
    except Exception as e:
        print(f"An error occurred during __main__ example: {e}")
