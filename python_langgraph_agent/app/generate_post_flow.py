from typing import Dict, Any, Literal, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError, NodeInterrupt as Interrupt # For max condense count & handling interrupts

from .state import GeneratePostState
from .models import ComplexPost, ImageModel # If needed by conditional edges, though mostly state fields

# Import core nodes
from .nodes.auth_socials import auth_socials_passthrough
from .nodes.content_generation_nodes import (
    generate_content_report_node,
    generate_post_node,
    condense_post_node,
    rewrite_post_node,
    rewrite_post_with_split_url_node
)
from .nodes.interaction_nodes import (
    human_node_placeholder,
    schedule_post_node,
    update_scheduled_date_node
)

# Import subgraphs
from .subgraphs.verify_links_graph import verify_links_graph
from .subgraphs.find_images_graph import find_images_graph

# Import utilities if needed by conditionals (e.g. isTextOnly from utils.py)
from .utils import is_text_only # Assuming is_text_only is ported to utils.py

# --- Node Names (Constants for clarity) ---
AUTH_SOCIALS_NODE = "auth_socials"
VERIFY_LINKS_SUBGRAPH_NODE = "verify_links_subgraph"
GENERATE_CONTENT_REPORT_NODE = "generate_content_report"
GENERATE_POST_NODE = "generate_post"
CONDENSE_POST_NODE = "condense_post"
FIND_IMAGES_SUBGRAPH_NODE = "find_images_subgraph"
HUMAN_NODE = "human_review" # Placeholder for human_node_placeholder
REWRITE_POST_NODE = "rewrite_post"
REWRITE_WITH_SPLIT_URL_NODE = "rewrite_with_split_url"
UPDATE_SCHEDULE_DATE_NODE = "update_schedule_date"
SCHEDULE_POST_NODE = "schedule_post"
# CURATED_POST_INTERRUPT_NODE = "curated_post_interrupt" # Placeholder for future

# --- Conditional Edge Functions ---

# TODO: Port `checkIfUrlsArePreviouslyUsed` from TS `generate-post-graph.ts` to utils.py
# For now, this conditional edge will be simplified.
async def generate_report_or_end_conditional_edge(state: GeneratePostState, config: Dict[str, Any]) -> Literal["generate_content_report", "END"]:
    """
    Original: generateReportOrEndConditionalEdge
    Decides whether to generate a content report or end the graph.
    Ends if URLs were previously used or no page content was extracted.
    """
    # Simplification: TS version checks `checkIfUrlsArePreviouslyUsed` and `!state.pageContents?.length`
    # For now, only check pageContents. `checkIfUrlsArePreviouslyUsed` needs a store/DB.
    # skip_used_urls_check = config.configurable.get("skipUsedUrlsCheck", False) # from utils.py if ported

    if not state.pageContents or len(state.pageContents) == 0:
        print("DEBUG: generate_report_or_end_conditional_edge -> END (no page content)")
        return END
    print("DEBUG: generate_report_or_end_conditional_edge -> generate_content_report")
    return GENERATE_CONTENT_REPORT_NODE

def route_after_generating_report(state: GeneratePostState) -> Literal["generate_post", "END"]:
    """
    Original: routeAfterGeneratingReport
    If a report was generated, proceed to generate post, otherwise end.
    """
    if state.report and state.report.strip() != "":
        print("DEBUG: route_after_generating_report -> generate_post")
        return GENERATE_POST_NODE
    print("DEBUG: route_after_generating_report -> END (no report generated or report is empty)")
    return END

MAX_CONDENSE_ATTEMPTS = 3 # As in TS version

async def condense_or_human_conditional_edge(state: GeneratePostState, config: Dict[str, Any]) -> Literal["condense_post", "find_images_subgraph", "human_review", "END"]:
    """
    Original: condenseOrHumanConditionalEdge
    If post is too long and condenseCount is low, try to condense.
    Else, if not text_only mode, find images.
    Else, go to human review.
    """
    # TODO: Port `removeUrls` utility from TS `utils.ts`
    # cleaned_post_length = len(removeUrls(state.post or "")) # Using state.post directly for now
    cleaned_post_length = len(state.post or "")

    if cleaned_post_length > 280 and state.condenseCount < MAX_CONDENSE_ATTEMPTS:
        print(f"DEBUG: condense_or_human_conditional_edge -> condense_post (length {cleaned_post_length}, count {state.condenseCount})")
        return CONDENSE_POST_NODE

    if state.condenseCount >= MAX_CONDENSE_ATTEMPTS and cleaned_post_length > 280:
        print(f"ERROR: Post still too long after {MAX_CONDENSE_ATTEMPTS} attempts. Length: {cleaned_post_length}. Going to END.")
        # This is a terminal failure for this path. In TS it routes to humanNode/findImages.
        # For robustness, we might send to human review or a specific error handler.
        # Following TS logic, it doesn't END here but proceeds. Let's match that.
        # The TS graph proceeds to findImages or humanNode after max condensation attempts.

    # text_only_mode = is_text_only(config) # from utils.py, assuming it's ported
    text_only_mode_from_config = config.get("configurable", {}).get("textOnlyMode", False) # Simplified access

    if not text_only_mode_from_config:
        print("DEBUG: condense_or_human_conditional_edge -> find_images_subgraph (not text_only mode)")
        return FIND_IMAGES_SUBGRAPH_NODE
    else:
        # If text_only, skip find_images and go to the human review (or curated interrupt logic)
        # For now, simplifying the curated interrupt part.
        print("DEBUG: condense_or_human_conditional_edge -> human_review (text_only mode)")
        return HUMAN_NODE # Simplified: directly to human_review

async def route_to_curated_interrupt_or_continue(state: GeneratePostState, config: Dict[str, Any]) -> Literal["human_review", "END"]:
    """
    Original: routeToCuratedInterruptOrContinue
    If origin is 'curate-data', routes to a different interrupt graph.
    For now, this placeholder will always route to the standard human_review node.
    """
    origin = config.get("configurable", {}).get("origin")
    if origin == "curate-data":
        print(f"DEBUG: route_to_curated_interrupt_or_continue -> human_review (origin: {origin}, simplified from curated_post_interrupt)")
        # TODO: Implement actual curated_post_interrupt graph invocation if needed.
        # This would involve:
        # client = langgraph_sdk.Client(...)
        # client.runs.create(thread_id, "curated_post_interrupt", input=state, config=...)
        # return END (as the main graph's work for this instance is done, handed off)
        # For now, route to human_review for simplicity in this graph.
        return HUMAN_NODE
    print("DEBUG: route_to_curated_interrupt_or_continue -> human_review (standard flow)")
    return HUMAN_NODE


def rewrite_or_end_conditional_edge(state: GeneratePostState) -> Literal["rewrite_post", "schedule_post", "update_schedule_date", "human_review", "rewrite_with_split_url", "END"]:
    """
    Original: rewriteOrEndConditionalEdge
    Routes based on state.next_node_action (which is 'next' in TS state).
    This field is populated by the human_node (or the system resuming from it).
    """
    next_action = state.next_node_action
    print(f"DEBUG: rewrite_or_end_conditional_edge -> next_action: {next_action}")
    if next_action == "rewritePost":
        return REWRITE_POST_NODE
    if next_action == "schedulePost":
        return SCHEDULE_POST_NODE
    if next_action == "updateScheduleDate":
        return UPDATE_SCHEDULE_DATE_NODE
    if next_action == "rewriteWithSplitUrl":
        return REWRITE_WITH_SPLIT_URL_NODE
    if next_action == "unknownResponse": # User response was unclear from human_node
        return HUMAN_NODE # Go back to human for clarification
    if next_action == "END": # User chose to discard or action completed
        return END

    # Default if next_node_action is not set or unrecognized after human_node
    # This shouldn't happen if human_node always sets a valid 'next_node_action' or raises Interrupt.
    # If human_node was skipped, or if it's the first pass, this edge isn't used.
    # This edge is specifically *from* human_node.
    print(f"WARN: rewrite_or_end_conditional_edge: Unspecified or unhandled next_action '{next_action}'. Defaulting to END.")
    return END


# --- Graph Definition ---
graph_builder = StateGraph(GeneratePostState)

# Add Nodes
graph_builder.add_node(AUTH_SOCIALS_NODE, auth_socials_passthrough)
graph_builder.add_node(VERIFY_LINKS_SUBGRAPH_NODE, verify_links_graph) # Subgraph
graph_builder.add_node(GENERATE_CONTENT_REPORT_NODE, generate_content_report_node)
graph_builder.add_node(GENERATE_POST_NODE, generate_post_node)
graph_builder.add_node(CONDENSE_POST_NODE, condense_post_node)
graph_builder.add_node(FIND_IMAGES_SUBGRAPH_NODE, find_images_graph) # Subgraph
graph_builder.add_node(HUMAN_NODE, human_node_placeholder) # Placeholder for HITL
graph_builder.add_node(REWRITE_POST_NODE, rewrite_post_node)
graph_builder.add_node(REWRITE_WITH_SPLIT_URL_NODE, rewrite_post_with_split_url_node)
graph_builder.add_node(UPDATE_SCHEDULE_DATE_NODE, update_scheduled_date_node)
graph_builder.add_node(SCHEDULE_POST_NODE, schedule_post_node)

# Define Edges
graph_builder.add_edge(START, AUTH_SOCIALS_NODE)
graph_builder.add_edge(AUTH_SOCIALS_NODE, VERIFY_LINKS_SUBGRAPH_NODE)

graph_builder.add_conditional_edges(
    VERIFY_LINKS_SUBGRAPH_NODE,
    generate_report_or_end_conditional_edge,
    {GENERATE_CONTENT_REPORT_NODE: GENERATE_CONTENT_REPORT_NODE, END: END}
)

graph_builder.add_conditional_edges(
    GENERATE_CONTENT_REPORT_NODE,
    route_after_generating_report,
    {GENERATE_POST_NODE: GENERATE_POST_NODE, END: END}
)

graph_builder.add_conditional_edges(
    GENERATE_POST_NODE,
    condense_or_human_conditional_edge,
    {
        CONDENSE_POST_NODE: CONDENSE_POST_NODE,
        FIND_IMAGES_SUBGRAPH_NODE: FIND_IMAGES_SUBGRAPH_NODE,
        HUMAN_NODE: HUMAN_NODE, # Path if text_only and no condense needed
        END: END # Should not be hit directly from here by design
    }
)

graph_builder.add_conditional_edges(
    CONDENSE_POST_NODE,
    condense_or_human_conditional_edge, # Same logic after condensing
    {
        CONDENSE_POST_NODE: CONDENSE_POST_NODE, # Loop to condense further if still too long
        FIND_IMAGES_SUBGRAPH_NODE: FIND_IMAGES_SUBGRAPH_NODE,
        HUMAN_NODE: HUMAN_NODE, # Path if text_only
        END: END # Should not be hit by design here
    }
)

graph_builder.add_conditional_edges(
    FIND_IMAGES_SUBGRAPH_NODE,
    route_to_curated_interrupt_or_continue, # Decides if standard human review or special interrupt
    {HUMAN_NODE: HUMAN_NODE, END: END} # Simplified: always to HUMAN_NODE or END
)

# Edges from Human Node based on user's choice (state.next_node_action)
graph_builder.add_conditional_edges(
    HUMAN_NODE,
    rewrite_or_end_conditional_edge,
    {
        REWRITE_POST_NODE: REWRITE_POST_NODE,
        SCHEDULE_POST_NODE: SCHEDULE_POST_NODE,
        UPDATE_SCHEDULE_DATE_NODE: UPDATE_SCHEDULE_DATE_NODE,
        HUMAN_NODE: HUMAN_NODE, # For 'unknownResponse', loop back
        REWRITE_WITH_SPLIT_URL_NODE: REWRITE_WITH_SPLIT_URL_NODE,
        END: END
    }
)

# Edges from rewrite/update nodes back to Human Node for review
graph_builder.add_edge(REWRITE_POST_NODE, HUMAN_NODE)
graph_builder.add_edge(UPDATE_SCHEDULE_DATE_NODE, HUMAN_NODE)
graph_builder.add_edge(REWRITE_WITH_SPLIT_URL_NODE, HUMAN_NODE)

# Final action node to END
graph_builder.add_edge(SCHEDULE_POST_NODE, END)


# Compile the graph
from langgraph.checkpoint.memory import MemorySaver # Import MemorySaver
memory = MemorySaver() # Instantiate checkpointer

try:
    generate_post_graph = graph_builder.compile(checkpointer=memory) # Add checkpointer
    generate_post_graph.name = "Generate Post Graph (Python with Checkpointing)"
    print("DEBUG: generate_post_graph compiled successfully with MemorySaver.")
except GraphRecursionError as e:
    print(f"ERROR: Graph compilation failed due to potential recursion: {e}")
    print("This might be due to MAX_CONDENSE_ATTEMPTS logic or other loops not having a guaranteed exit to END under all conditions.")
    generate_post_graph = None # Ensure it's None if compilation fails
except Exception as e:
    print(f"ERROR: Graph compilation failed with an unexpected error: {e}")
    generate_post_graph = None


if __name__ == '__main__':
    # Basic test to invoke the graph (will require proper setup for clients, API keys, etc.)
    # And a way to handle interrupts from human_node and auth_socials

    async def run_main_graph_example():
        if not generate_post_graph:
            print("Graph not compiled, cannot run example.")
            return

        print("\n--- Running Main generate_post_graph Example ---")

        # Initial state for the graph
        initial_graph_state = GeneratePostState(
            links=["https://blog.langchain.dev/langgraph-cloud/"],
            # Configurable fields are passed in the `config` dict for `astream` or `ainvoke`
        )

        graph_config = {
            "configurable": {
                "user_id": "test_user@example.com", # For Arcade
                "textOnlyMode": False, # Test with image finding
                # "skipUsedUrlsCheck": True, # If implemented
                # "skipContentRelevancyCheck": True, # If implemented
            }
        }

        print(f"Initial State: {initial_graph_state.model_dump(exclude_none=True)}")
        print(f"Run Config: {graph_config}")

        try:
            # Stream events to see the flow
            async for event in generate_post_graph.astream(initial_graph_state, config=graph_config):
                print("\nGraph Event:")
                for key, value in event.items():
                    # Truncate long values for cleaner logging
                    if isinstance(value, GeneratePostState):
                        print(f"  {key}: State (see details below)")
                        # print(f"    pageContents: {value.pageContents}")
                        # print(f"    report: {value.report[:100] if value.report else 'None'}...")
                        # print(f"    post: {value.post[:100] if value.post else 'None'}...")
                        # print(f"    imageOptions: {value.imageOptions}")
                        # print(f"    image: {value.image}")
                        # print(f"    next_node_action: {value.next_node_action}")
                        # print(f"    pending_arcade_auth: {value.pending_arcade_auth}")
                    elif isinstance(value, dict) and "report" in value:
                         print(f"  {key}: { {k: (str(v)[:100] + '...' if isinstance(v, str) and len(v) > 100 else v) for k,v in value.items()} }")
                    elif isinstance(value, str) and len(value) > 150:
                        print(f"  {key}: {value[:150]}...")
                    else:
                        print(f"  {key}: {value}")

                # This basic example doesn't fully handle resumable interrupts from CLI.
                # It will print events until an Interrupt is raised.
                pass # End of simple event printing

        except Interrupt as e:
            print(f"\n--- GRAPH INTERRUPTED ---")
            interrupt_data = e.data
            print(f"Interrupt Title: {interrupt_data.get('title')}")
            print(f"Interrupt Description:\n{interrupt_data.get('description')}")

            current_interrupted_state = initial_graph_state # This is a simplification.
            # In a real resumable flow, we'd get the state from the interrupt/checkpoint.
            # For this CLI demo, we'll assume the interrupt happened and we have 'initial_graph_state'
            # as the basis, and we'll construct the next state based on user input.

            next_run_state_update = {}

            if interrupt_data.get("title") == "Human Review Required":
                print("\n--- Human Review Required (CLI Interaction) ---")
                print(f"Current Post Content:\n{interrupt_data.get('current_post_content')}")
                print(f"Image URL: {interrupt_data.get('image_url')}")
                print(f"Scheduled Date: {interrupt_data.get('current_schedule_date')}")

                print("\nAvailable Actions:")
                actions_map = {str(i+1): action["id"] for i, action in enumerate(interrupt_data.get("available_actions", []))}
                for i, action in enumerate(interrupt_data.get("available_actions", [])):
                    print(f"  {i+1}. {action['label']} ({action['id']})")

                while True:
                    choice = input("Choose action (number): ")
                    chosen_action_id = actions_map.get(choice)
                    if chosen_action_id:
                        next_run_state_update["next_node_action"] = chosen_action_id
                        break
                    print("Invalid choice. Try again.")

                if chosen_action_id == "rewritePost":
                    feedback = input("Enter feedback for rewrite: ")
                    next_run_state_update["userResponse"] = feedback
                elif chosen_action_id == "updateScheduleDate":
                    new_date_str = input("Enter new schedule date (e.g., YYYY-MM-DD, 'tomorrow', 'p1'): ")
                    next_run_state_update["userResponse"] = new_date_str # The node will parse this

                # Update initial_graph_state for the "next run" simulation
                # This isn't true checkpoint resume, but a way to continue flow via CLI
                updated_input_state = initial_graph_state.model_copy(update=next_run_state_update)

                if chosen_action_id != "discard": # "discard" means END, so no next run needed for it
                    print(f"\n--- Resuming graph with action: {chosen_action_id} ---")
                    # This is a new run, but with state reflecting the decision.
                    async for event in generate_post_graph.astream(updated_input_state, config=graph_config):
                        print("\nGraph Event (after human input):")
                        for key, value in event.items():
                            # Simplified logging for resumed run
                            if isinstance(value, str) and len(value) > 150: print(f"  {key}: {value[:150]}...")
                            else: print(f"  {key}: {value}")
                else:
                    print("--- Post discarded by user ---")


            elif interrupt_data.get("title") == "Social Media Authorization Needed":
                print("\n--- Authorization Required (CLI Interaction) ---")
                print("Auth Actions/Links:")
                for key, url_val in interrupt_data.get("actions", {}).items():
                    print(f"  {key}: {url_val}")

                input("Simulate opening browser, authorizing, then press Enter to continue...")

                pending_info = interrupt_data.get("pending_arcade_auth_info")
                if pending_info:
                    next_run_state_update["pending_arcade_auth"] = pending_info

                # Update initial_graph_state for the "next run" simulation
                updated_input_state = initial_graph_state.model_copy(update=next_run_state_update)

                print(f"\n--- Resuming graph after simulated authorization ---")
                async for event in generate_post_graph.astream(updated_input_state, config=graph_config):
                    print("\nGraph Event (after auth attempt):")
                    for key, value in event.items():
                        if isinstance(value, str) and len(value) > 150: print(f"  {key}: {value[:150]}...")
                        else: print(f"  {key}: {value}")

            else:
                print(f"Unhandled Interrupt Type: {interrupt_data.get('title')}")

        except Exception as e:
            import traceback
            print(f"\n--- An Unexpected Error Occurred During Graph Execution ---")
            print(f"Error Type: {type(e)}")
            print(f"Error Message: {e}")
            print(traceback.format_exc())


    if __name__ == "__main__":
        # This import needs to be here or handled by PYTHONPATH for direct script run
        import sys
        import pathlib
        # Add project root to path if running script directly for imports to work
        project_root = pathlib.Path(__file__).resolve().parent.parent.parent
        # sys.path.insert(0, str(project_root / "python_langgraph_agent")) # If app is not a top-level package
        # sys.path.insert(0, str(project_root)) # If python_langgraph_agent is a top-level package

        # Load .env for API keys
        from dotenv import load_dotenv
        env_path_project_root = project_root / '.env'
        env_path_agent_root = project_root / 'python_langgraph_agent' / '.env'

        if env_path_project_root.exists(): load_dotenv(dotenv_path=env_path_project_root)
        elif env_path_agent_root.exists(): load_dotenv(dotenv_path=env_path_agent_root)
        else: print("DEBUG: No .env found for main_graph example run.")

        # Ensure utils.py has is_text_only (it's not used by conditionals yet, but good for completeness)
        # For now, manually ensure is_text_only can be imported or its usage is guarded
        try:
            from .utils import is_text_only
        except ImportError:
            print("WARN: is_text_only could not be imported from utils.py. Ensure it's defined there.")
            # Define a dummy one for this test run if not present
            def is_text_only(config): return config.get("configurable",{}).get("textOnlyMode",False)


        import asyncio
        asyncio.run(run_main_graph_example())
