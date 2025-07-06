import streamlit as st
import os
from dotenv import load_dotenv
import pathlib

# --- Page Configuration ---
st.set_page_config(
    page_title="Social Media Agent (Python)",
    page_icon="🤖",
    layout="wide"
)

st.title("Social Media Agent 🐍")
st.caption("Convert URLs to social media posts with AI and human-in-the-loop review.")

# --- Environment Variable Loading ---
# Load .env file from the `python_langgraph_agent` directory if it exists
# This allows placing a .env file at the same level as streamlit_app.py
APP_DIR = pathlib.Path(__file__).resolve().parent
dotenv_path = APP_DIR / ".env"

if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
    st.sidebar.success(".env file loaded successfully!")
else:
    st.sidebar.info("No .env file found in the application directory. API keys should be set in the environment.")

# --- Initial Checks & Warnings ---
# Example: Check for Arcade API Key if Arcade auth is intended to be used by default
# The actual USE_ARCADE_AUTH check should come from your utils or config system
# For now, let's assume a simple os.getenv check for demonstration
USE_ARCADE_AUTH_ENV = os.getenv("USE_ARCADE_AUTH", "false").lower() == "true"
if USE_ARCADE_AUTH_ENV:
    if not os.getenv("ARCADE_API_KEY"):
        st.sidebar.warning("USE_ARCADE_AUTH is true, but ARCADE_API_KEY is not set. Arcade features may fail.")
    else:
        st.sidebar.info("Arcade API Key found (if USE_ARCADE_AUTH is true).")

if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"): # Assuming one of these might be used by LLMs
    st.sidebar.warning("No primary LLM API key (ANTHROPIC_API_KEY or OPENAI_API_KEY) found. LLM calls will fail.")


# --- Main App Area Placeholder ---
st.header("Agent Controls")

with st.form("generate_post_form"):
    st.subheader("Generate New Post")

    urls_input = st.text_area(
        "Enter URL(s) to process (one URL per line):",
        height=100,
        placeholder="https://blog.langchain.dev/example-post\nhttps://another-url.com/article"
    )

    col1, col2 = st.columns(2)
    with col1:
        text_only_mode = st.checkbox("Text-Only Mode", value=False, help="If checked, the agent will not attempt to find or use images, or process YouTube video content specifically.")
        arcade_user_id = st.text_input("Arcade User ID (Required if using Arcade Auth)", value="test_user@example.com", help="Your application's unique ID for the user (e.g., email, UUID). Needed if USE_ARCADE_AUTH is true.")

    with col2:
        post_to_linkedin_org = st.checkbox("Post to LinkedIn Organization", value=False, help="If checked, will attempt to post to the configured LinkedIn Organization page. Requires LINKEDIN_ORGANIZATION_ID to be set.")
        # Add other configurable fields here as needed, e.g., skip_content_relevancy_check

    submit_button = st.form_submit_button("🚀 Generate Post")

if submit_button:
    st.session_state.run_in_progress = True # Flag to indicate a run has started
    st.session_state.error_message = None # Clear previous errors
    st.session_state.interrupt_data = None # Clear previous interrupt data
    st.session_state.log_messages = [] # For logging graph events
    st.session_state.final_graph_output = None

    links = [url.strip() for url in urls_input.split("\n") if url.strip()]

    if not links:
        st.error("Please enter at least one URL.")
        st.session_state.run_in_progress = False
    else:
        st.info(f"Starting post generation for {len(links)} URL(s)...")
        # Store inputs for potential re-runs or if needed by graph logic later
        st.session_state.current_input_links = links
        st.session_state.current_config_text_only = text_only_mode
        st.session_state.current_config_post_to_linkedin_org = post_to_linkedin_org
        st.session_state.current_config_arcade_user_id = arcade_user_id

# --- Imports for Graph Logic (moved to top) ---
import asyncio
import uuid
from app.generate_post_flow import generate_post_graph
from app.state import GeneratePostState
from app.state import TEXT_ONLY_MODE_KEY, POST_TO_LINKEDIN_ORGANIZATION_KEY # For config keys
from langgraph.errors import NodeInterrupt as Interrupt # For catching interrupts

# --- Initialize Session State ---
if "run_in_progress" not in st.session_state:
    st.session_state.run_in_progress = False
    st.session_state.log_messages = []
    st.session_state.interrupt_data = None
    st.session_state.error_message = None
    st.session_state.final_graph_output = None
    st.session_state.current_graph_input_state = None # Will hold GeneratePostState object for current/next run
    st.session_state.active_thread_id = None # For config and checkpointing
    # For specific resume actions
    st.session_state.resume_auth_button_clicked = False
    st.session_state.resume_human_review_action = None # Stores action like 'schedulePost'
    st.session_state.human_review_feedback = "" # For rewrite feedback
    st.session_state.human_review_new_date = "" # For new schedule date

# --- Async Graph Runner Function ---
async def run_graph_async_logic(input_state: GeneratePostState, config: dict):
    """
    Runs the LangGraph graph using astream and updates session_state.
    This function itself does not call st.experimental_rerun().
    It expects run_in_progress to be set to True by the caller.
    """
    # st.session_state.run_in_progress = True # Caller now handles setting this to True
    st.session_state.interrupt_data = None # Clear previous interrupt before new run/resume
    st.session_state.error_message = None  # Clear previous error

    # Accumulate state updates locally for this run to determine final state if graph completes
    # This is a workaround until proper checkpointing state retrieval is implemented
    current_accumulated_state_dict = input_state.model_dump()

    try:
        async for event_part in generate_post_graph.astream(input_state, config=config, stream_mode="updates"):
            for node_name, output_delta in event_part.items(): # output_delta contains changes from this node
                log_entry = f"Event from Node: **{node_name}**"
                st.session_state.log_messages.append(log_entry)
                if isinstance(output_delta, dict):
                    current_accumulated_state_dict.update(output_delta) # Merge delta into our accumulated state
                    output_summary = {k: (str(v)[:100] + '...' if isinstance(v, str) and len(v) > 100 else v) for k, v in output_delta.items()}
                    st.session_state.log_messages.append(f"```json\nOutput Delta: {output_summary}\n```")
                else: # Should not happen with StateGraph and Pydantic state if nodes return dicts
                    st.session_state.log_messages.append(f"Output: {str(output_delta)[:200]}")

                # Update st.session_state.current_graph_input_state with the accumulated state
                # so that if an interrupt happens *after* this node, the resume logic has the most recent full state.
                # This is crucial if not using a robust checkpointer that handles state recovery.
                st.session_state.current_graph_input_state = GeneratePostState(**current_accumulated_state_dict)

        # If loop completes without Interrupt, it means graph ENDed
        st.session_state.log_messages.append("Graph run completed successfully (reached END).")

        # With a checkpointer, get the definitive final state
        final_checkpoint = generate_post_graph.get_state(config) # config contains thread_id
        if final_checkpoint:
            final_state_obj = final_checkpoint.values # .values is the actual state object (e.g., GeneratePostState instance)
            st.session_state.final_graph_output = {
                "status": "Completed",
                "post": final_state_obj.post,
                "complexPost": final_state_obj.complexPost.model_dump() if final_state_obj.complexPost else None,
                "image": final_state_obj.image.model_dump() if final_state_obj.image else None,
                "report": final_state_obj.report,
                "links": final_state_obj.links,
                "scheduleDate": str(final_state_obj.scheduleDate) if final_state_obj.scheduleDate else None,
                # Optionally include the full state for debugging in the UI
                # "full_state_dump": final_state_obj.model_dump()
            }
        else:
            # Fallback if get_state returns None (should not happen if graph ended cleanly with checkpointer)
            st.session_state.log_messages.append("WARN: Could not retrieve final state from checkpointer. Using accumulated state.")
            final_state_obj_fallback = GeneratePostState(**current_accumulated_state_dict)
            st.session_state.final_graph_output = {
                "status": "Completed (fallback state)",
                "post": final_state_obj_fallback.post,
                # ... (populate other fields as above) ...
            }


    except Interrupt as e:
        # When an interrupt occurs, the state might not be fully checkpointed for the current node's partial work.
        # The st.session_state.current_graph_input_state (updated after each event part)
        # is important for the UI to show the most recent data before interruption.
        st.session_state.log_messages.append(f"--- GRAPH INTERRUPTED: {e.data.get('title', 'Unknown Interrupt')} ---")
        st.session_state.interrupt_data = e.data
        # Store the state at point of interruption if not using checkpointer that handles it automatically
        # For now, we assume interrupt_data + initial state is enough for resume logic
        # This might need refinement: if graph was partway, initial_state is not the "current" state.
        # However, our resume logic below re-constructs input state based on interrupt.
    except Exception as e:
        st.session_state.log_messages.append(f"--- GRAPH EXECUTION ERROR ---")
        st.session_state.error_message = f"An error occurred: {str(e)}"
        import traceback
        st.session_state.log_messages.append(f"```\n{traceback.format_exc()}\n```")
    finally:
        st.session_state.run_in_progress = False
        # Rerun is handled by the caller of this async function

# --- Resume Logic Handler (called before form processing) ---
if st.session_state.get("resume_auth_button_clicked", False):
    st.session_state.resume_auth_button_clicked = False # Consume flag

    if st.session_state.interrupt_data and st.session_state.current_graph_input_state and st.session_state.active_thread_id:
        st.session_state.log_messages.append("Resuming graph after user indicated authorization attempt...")

        current_state_for_resume = st.session_state.current_graph_input_state
        pending_info = st.session_state.interrupt_data.get("pending_arcade_auth_info")
        if pending_info:
            current_state_for_resume = current_state_for_resume.model_copy(update={"pending_arcade_auth": pending_info})

        st.session_state.current_graph_input_state = current_state_for_resume # Update the state for the run
        st.session_state.interrupt_data = None # Clear interrupt that's being handled

        graph_config_for_resume = {
            "configurable": {
                "thread_id": st.session_state.active_thread_id, # CRITICAL: use same thread_id
                "user_id": st.session_state.current_config_arcade_user_id,
                TEXT_ONLY_MODE_KEY: st.session_state.current_config_text_only,
                POST_TO_LINKEDIN_ORGANIZATION_KEY: st.session_state.current_config_post_to_linkedin_org,
            }
        }
        asyncio.run(run_graph_async_logic(st.session_state.current_graph_input_state, graph_config_for_resume))
        st.experimental_rerun() # Rerun to reflect changes


# --- Resume Logic Handler for Human Review ---
if st.session_state.get("human_action_taken"):
    action_id = st.session_state.human_action_taken
    st.session_state.human_action_taken = None # Consume the flag

    if st.session_state.current_graph_input_state and st.session_state.active_thread_id:
        st.session_state.log_messages.append(f"Resuming graph after human action: {action_id}")

        # current_graph_input_state should be the state at the point of interruption.
        # The human_node_placeholder interrupt_data contains display values.
        # We need to update the actual current_graph_input_state for the next run.

        state_update_for_resume = {"next_node_action": action_id, "userResponse": None}

        if action_id == "rewritePost":
            state_update_for_resume["userResponse"] = st.session_state.get("human_review_feedback", "")
            st.session_state.human_review_feedback = "" # Clear feedback after use
        elif action_id == "updateScheduleDate":
            state_update_for_resume["userResponse"] = st.session_state.get("human_review_new_date", "")
            st.session_state.human_review_new_date = "" # Clear new date input after use
        elif action_id == "discard":
            state_update_for_resume["next_node_action"] = "END"

        # Ensure current_graph_input_state is a GeneratePostState instance before model_copy
        if isinstance(st.session_state.current_graph_input_state, GeneratePostState):
            st.session_state.current_graph_input_state = st.session_state.current_graph_input_state.model_copy(update=state_update_for_resume)
        else:
            # This case implies current_graph_input_state was not properly set or maintained.
            # For robustness, one might try to reconstruct it if possible, or show an error.
            # For now, if it's not the right type, we can't safely proceed with model_copy.
            st.error("Error: Cannot resume, graph state is not in the expected format.")
            st.session_state.run_in_progress = False # Stop any spinners etc.
            st.stop() # Halt further script execution for this rerun

        st.session_state.interrupt_data = None # Clear the human review interrupt

        if action_id != "discard":
            # Reconstruct graph_config for resume
            graph_config_for_resume = {
                "configurable": {
                    "thread_id": st.session_state.active_thread_id,
                    "user_id": st.session_state.current_config_arcade_user_id,
                    TEXT_ONLY_MODE_KEY: st.session_state.current_config_text_only,
                    POST_TO_LINKEDIN_ORGANIZATION_KEY: st.session_state.current_config_post_to_linkedin_org,
                }
            }
            asyncio.run(run_graph_async_logic(st.session_state.current_graph_input_state, graph_config_for_resume))
        else:
            st.session_state.log_messages.append("Post discarded by user action.")
            st.session_state.run_in_progress = False # Ensure spinner stops
            st.success("Post discarded.") # User feedback

        st.experimental_rerun()


# --- Main App Area / Form ---
st.header("Agent Controls")

# ... (form definition remains the same) ...
# Modify form submission logic:
if submit_button: # This is from the st.form
    st.session_state.run_in_progress = True
    st.session_state.error_message = None
    st.session_state.interrupt_data = None
    st.session_state.log_messages = []
    st.session_state.final_graph_output = None

    links = [url.strip() for url in urls_input.split("\n") if url.strip()]

    if not links:
        st.error("Please enter at least one URL.")
        st.session_state.run_in_progress = False
    else:
        st.info(f"Starting post generation for {len(links)} URL(s)...")
        # Store inputs for potential re-runs or if needed by graph logic later
        st.session_state.current_input_links = links
        st.session_state.current_config_text_only = text_only_mode
        st.session_state.current_config_post_to_linkedin_org = post_to_linkedin_org
        st.session_state.current_config_arcade_user_id = arcade_user_id

        # This is a NEW run
        st.session_state.current_graph_input_state = GeneratePostState(links=st.session_state.current_input_links)
        st.session_state.active_thread_id = str(uuid.uuid4()) # New thread_id for new run

        graph_config = {
            "configurable": {
                "thread_id": st.session_state.active_thread_id,
                "user_id": st.session_state.current_config_arcade_user_id,
                TEXT_ONLY_MODE_KEY: st.session_state.current_config_text_only,
                POST_TO_LINKEDIN_ORGANIZATION_KEY: st.session_state.current_config_post_to_linkedin_org,
            }
        }
        st.session_state.log_messages.append(f"Starting new graph run. Config: {graph_config}")
        asyncio.run(run_graph_async_logic(st.session_state.current_graph_input_state, graph_config))
        st.experimental_rerun() # Rerun to reflect initial logs and spinner


# --- Display Area for Outputs/Logs/Interrupts (remains mostly the same) ---
st.divider()
st.header("Agent Output & Logs")

if st.session_state.run_in_progress:
    st.info("🤖 Agent run in progress...")
    with st.spinner("Thinking..."):
        # The spinner will show while the graph runs. Content below will update on rerun.
        pass # Actual graph running happens in the form submit logic

# Display logs
if st.session_state.log_messages:
    # Expand if there's an interrupt, error, or final output to see logs leading to it.
    # Otherwise, keep it collapsed for a clean UI during initial run or if only logs are present.
    is_significant_outcome = bool(st.session_state.interrupt_data or st.session_state.final_graph_output or st.session_state.error_message)
    # If a run just finished (not in progress anymore) and there was a result/error, expand.
    # If a run is fresh and in progress (and no significant outcome yet), keep collapsed.
    log_expanded_default = True if is_significant_outcome and not st.session_state.run_in_progress else False
    if not st.session_state.log_messages and not is_significant_outcome : # if only "starting..." log and nothing else yet.
        log_expanded_default = False


    with st.expander("Execution Log", expanded=log_expanded_default):
        for msg in st.session_state.log_messages:
            st.markdown(msg, unsafe_allow_html=True)

# Display interrupt data if any
if st.session_state.interrupt_data:
    with st.expander("⚠️ Action Required - INTERRUPT", expanded=True):
        st.subheader(st.session_state.interrupt_data.get("title", "Interrupt Occurred"))
        st.markdown(st.session_state.interrupt_data.get("description", "No description provided."))

        interrupt_actions = st.session_state.interrupt_data.get("actions")
        if interrupt_actions and isinstance(interrupt_actions, dict):
            st.markdown("**Suggested Actions/Links:**")
            for action_key, action_val in interrupt_actions.items():
                if isinstance(action_val, str) and action_val.startswith("http"):
                    st.markdown(f"- [{action_key.replace('URL','').capitalize()}]({action_val})")
                else:
                    st.markdown(f"- **{action_key.replace('URL','').capitalize()}:** `{action_val}`")

        # Add button for auth interrupt
        if st.session_state.interrupt_data.get("title") == "Social Media Authorization Needed":
            if st.button("✅ I have authorized / Retry Authorization", key="resume_auth_button"):
                # This button click will cause a rerun.
                # The actual resume logic will be handled at the top of the script
                # or before the main form processing.
                # We set a flag to indicate this button was pressed.
                st.session_state.resume_auth_button_clicked = True
                st.experimental_rerun() # Explicitly rerun to process the click at the top

                st.experimental_rerun() # Explicitly rerun to process the click at the top

        elif st.session_state.interrupt_data.get("title") == "Human Review Required":
            interrupt_payload = st.session_state.interrupt_data

            st.subheader("📝 Human Review Required")
            st.markdown("**Please review the generated post and take action:**")

            # Display Post Content
            post_content_to_display = interrupt_payload.get('current_post_content', 'N/A')
            if "Main:" in post_content_to_display and "Reply:" in post_content_to_display: # Crude check for complex post
                parts = post_content_to_display.split("Reply:", 1)
                main_post_part = parts[0].replace("Main:", "").strip()
                reply_post_part = parts[1].strip() if len(parts) > 1 else ""
                with st.container(border=True):
                    st.markdown("**Main Post Draft:**")
                    st.markdown(main_post_part) # Render as markdown
                if reply_post_part:
                    with st.container(border=True):
                        st.markdown("**Reply Draft:**")
                        st.markdown(reply_post_part) # Render as markdown
            else:
                with st.container(border=True):
                    st.markdown("**Post Draft:**")
                    st.markdown(post_content_to_display) # Render as markdown

            # Display Image
            image_url_to_display = interrupt_payload.get('image_url')
            if image_url_to_display and image_url_to_display != "No image selected.":
                with st.container(border=True):
                    st.markdown("**Selected Image:**")
                    st.image(image_url_to_display, caption="Image Preview", use_column_width=True)
            else:
                st.info("No image selected for this post.")

            # Display Context
            with st.expander("Contextual Information", expanded=False):
                st.write(f"**Original Links Processed:** {interrupt_payload.get('links_in_post', [])}")
                st.write(f"**Current Schedule Date:** {interrupt_payload.get('current_schedule_date', 'Not scheduled')}")

            st.divider()
            st.markdown("**Choose an action:**")

            available_actions = interrupt_payload.get("available_actions", [])

            # Layout actions in columns for better UI if many actions
            cols = st.columns(len(available_actions) if len(available_actions) <= 3 else 3)
            action_col_idx = 0

            for action in available_actions:
                action_id = action["id"]
                action_label = action["label"]
                current_col = cols[action_col_idx % len(cols)]

                if action_id == "rewritePost":
                    st.session_state.human_review_feedback = st.text_area("Feedback for rewrite:", key="human_feedback_text", value=st.session_state.get("human_review_feedback", ""))
                    if st.button(action_label, key=f"human_action_{action_id}"):
                        st.session_state.human_action_taken = action_id
                        # Feedback is already in st.session_state.human_review_feedback
                        st.experimental_rerun()
                elif action_id == "updateScheduleDate":
                    st.session_state.human_review_new_date = st.text_input("New schedule date/time (e.g., 'tomorrow 2pm', '2024-12-25 09:00', 'p1'):", key="human_new_date_text", value=st.session_state.get("human_review_new_date", ""))
                    if st.button(action_label, key=f"human_action_{action_id}"):
                        st.session_state.human_action_taken = action_id
                        # New date is in st.session_state.human_review_new_date
                        st.experimental_rerun()
                else: # Simple button actions like schedulePost, discard, rewriteWithSplitUrl
                    # Use columns for these buttons
                    if current_col.button(action_label, key=f"human_action_{action_id}"):
                        st.session_state.human_action_taken = action_id
                        st.experimental_rerun()
                action_col_idx +=1

# Display final output if graph completed
if st.session_state.final_graph_output:
    st.success("✅ Graph Run Completed!")
    output = st.session_state.final_graph_output

    with st.container(border=True):
        st.subheader("Final Output")
        if output.get("complexPost"):
            st.markdown("**Main Post:**")
            st.markdown(output["complexPost"]["main_post"])
            if output["complexPost"]["reply_post"]:
                st.markdown("---")
                st.markdown("**Reply Post:**")
                st.markdown(output["complexPost"]["reply_post"])
        elif output.get("post"):
            st.markdown("**Generated Post:**")
            st.markdown(output["post"])
        else:
            st.info("No final post content was generated or captured in the output.")

        if output.get("image") and output["image"].get("imageUrl"):
            st.markdown("---")
            st.markdown("**Selected Image:**")
            st.image(output["image"]["imageUrl"], caption=output["image"].get("mimeType", "Image Preview"))
        else:
            st.info("No image was selected for the post.")

        if output.get("report"):
            with st.expander("View Generated Report", expanded=False):
                st.markdown(output["report"])

        with st.expander("View Full Final State (JSON)", expanded=False):
            st.json(output) # Show all collected final data

# Display error message if any
if st.session_state.error_message:
    st.error(st.session_state.error_message)


# Placeholder for future content
# st.divider()
# st.header("Agent Output")
# st.write("Agent's responses and generated content will be displayed here.")


if __name__ == '__main__':
    # To run this app:
    # 1. Ensure you are in the `python_langgraph_agent` directory.
    # 2. Run `poetry install` if you haven't already.
    # 3. Run `poetry run streamlit run streamlit_app.py`
    st.sidebar.markdown("---")
    st.sidebar.markdown("### How to Run:")
    st.sidebar.code("cd python_langgraph_agent\npoetry run streamlit run streamlit_app.py")
    st.balloons()
