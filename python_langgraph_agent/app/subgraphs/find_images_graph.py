from langgraph.graph import StateGraph, START, END
from ..state import GeneratePostState # Main state used by this subgraph
from ..nodes.find_images_nodes import (
    find_images_node,
    validate_images_node,
    re_rank_images_node
)

# Define node names as constants for clarity
FIND_IMAGES_NODE = "find_images_actual_node" # Renamed to avoid conflict with imported function
VALIDATE_IMAGES_NODE = "validate_images_actual_node"
RE_RANK_IMAGES_NODE = "re_rank_images_actual_node"

def validate_images_or_end(state: GeneratePostState) -> str:
    """
    Conditional edge: if imageOptions has items, go to validateImages, otherwise END.
    """
    if state.imageOptions and len(state.imageOptions) > 0:
        print(f"DEBUG: find_images_graph - {len(state.imageOptions)} image options found, proceeding to validate.")
        return VALIDATE_IMAGES_NODE
    else:
        print("DEBUG: find_images_graph - No image options found by find_images_node, ending subgraph.")
        return END

# Create the StateGraph using GeneratePostState
# This subgraph reads from and writes to the main GeneratePostState fields
find_images_workflow = StateGraph(GeneratePostState)

# Add the nodes
find_images_workflow.add_node(FIND_IMAGES_NODE, find_images_node)
find_images_workflow.add_node(VALIDATE_IMAGES_NODE, validate_images_node)
find_images_workflow.add_node(RE_RANK_IMAGES_NODE, re_rank_images_node)

# Define the graph structure (edges)
find_images_workflow.add_edge(START, FIND_IMAGES_NODE)

find_images_workflow.add_conditional_edges(
    FIND_IMAGES_NODE,
    validate_images_or_end,
    {
        VALIDATE_IMAGES_NODE: VALIDATE_IMAGES_NODE, # Path if condition returns this string
        END: END  # Path if condition returns END
    }
)

find_images_workflow.add_edge(VALIDATE_IMAGES_NODE, RE_RANK_IMAGES_NODE)
find_images_workflow.add_edge(RE_RANK_IMAGES_NODE, END)

# Compile the graph
find_images_graph = find_images_workflow.compile()
find_images_graph.name = "Find Images Subgraph"


if __name__ == '__main__':
    import asyncio
    from ...state import ImageModel # For constructing initial state with ImageModel

    async def run_example():
        # Example 1: Has image options that get validated and one selected
        initial_state_1 = GeneratePostState(
            relevantLinks=["https://example.com/article1"],
            report="This is a report about an exciting topic.",
            post="A generated post about the exciting topic.",
            # imageOptions will be populated by find_images_node
        )
        print("--- Running Example 1: Images Found ---")
        async for event in find_images_graph.astream(initial_state_1):
            print(f"Event: {event}")
            if END in event:
                final_state_1 = event[END]
                print(f"Final State (Example 1 Image): {final_state_1.get('image')}")
                print(f"Final State (Example 1 Image Options): {final_state_1.get('imageOptions')}")


        # Example 2: find_images_node returns no options initially (mock it by overriding)
        class MockFindImagesNoResult(GeneratePostState):
            pass # Will use default empty imageOptions

        async def find_images_no_results_node(state: MockFindImagesNoResult):
            print("DEBUG: Mocked find_images_node - returning NO image options")
            return {"imageOptions": []}

        # Temporarily swap out the node for testing this path
        original_find_node = find_images_workflow.nodes[FIND_IMAGES_NODE]
        find_images_workflow.nodes[FIND_IMAGES_NODE].func = find_images_no_results_node
        # Recompile because we changed a node.
        # Note: Modifying compiled graphs or their internal nodes like this is for testing/illustration.
        # In real usage, you'd compile once.
        # For robust testing, it's better to parameterize nodes or use dependency injection.

        # Recompile (or create a new graph instance for the test)
        # For simplicity, we'll assume this direct modification works for this test context.
        # A cleaner way would be:
        # test_graph_no_images = StateGraph(GeneratePostState)
        # ... add nodes ... (with find_images_no_results_node) ... compile ...
        # But this is fine for a quick test of the conditional edge.

        # Re-compile is needed if node function is changed on the workflow object
        recompiled_graph_for_test = find_images_workflow.compile()


        initial_state_2 = MockFindImagesNoResult(
            relevantLinks=["https://example.com/article2"],
            report="Report for article 2.",
            post="Post for article 2.",
        )
        print("\n--- Running Example 2: No Images Found by find_images_node ---")
        async for event in recompiled_graph_for_test.astream(initial_state_2):
            print(f"Event: {event}")
            if END in event:
                final_state_2 = event[END]
                print(f"Final State (Example 2 Image): {final_state_2.get('image')}") # Should be None
                print(f"Final State (Example 2 Image Options): {final_state_2.get('imageOptions')}") # Should be []

        # Restore original node if further tests were needed on the same workflow object
        find_images_workflow.nodes[FIND_IMAGES_NODE].func = original_find_node.func


    asyncio.run(run_example())
