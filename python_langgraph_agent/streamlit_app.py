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
    """
    st.session_state.run_in_progress = True
    st.session_state.interrupt_data = None # Clear previous interrupt before new run/resume
    st.session_state.error_message = None  # Clear previous error

    try:
        async for event_part in generate_post_graph.astream(input_state, config=config, stream_mode="updates"):
            for node_name, output in event_part.items():
                log_entry = f"Event from Node: **{node_name}**"
                st.session_state.log_messages.append(log_entry)
                if isinstance(output, dict):
                    output_summary = {k: (str(v)[:100] + '...' if isinstance(v, str) and len(v) > 100 else v) for k, v in output.items()}
                    st.session_state.log_messages.append(f"```json\nOutput: {output_summary}\n```")
                else:
                    st.session_state.log_messages.append(f"Output: {str(output)[:200]}")

                # Persist the latest full state if possible (or relevant parts for resume)
                # If the event contains the full state object for the node, we can store it.
                # For "updates" mode, `output` is the delta. The full state is managed by the checkpointer.
                # If not using a checkpointer that `astream` can use to give us full state,
                # we might need to manually accumulate state or get it from the interrupt.
                # For now, we rely on interrupt data or final output.
                # Let's assume `st.session_state.current_graph_input_state` is the one to be updated for resume.
                # This is complex without proper checkpointing.
                # The `input_state` for the *next* call to astream should be the one from the interrupt.
                # The `human_node_placeholder` includes current_post_content in its interrupt_data.
                # `auth_socials_passthrough` includes pending_arcade_auth_info.

        st.session_state.log_messages.append("Graph run completed successfully.")
        # st.session_state.final_graph_output = ... # Extract from last event if needed

    except Interrupt as e:
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
    with st.expander("Execution Log", expanded=True):
        for msg in st.session_state.log_messages:
            st.markdown(msg, unsafe_allow_html=True) # Use markdown for potential formatting

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

        elif st.session_state.interrupt_data.get("title") == "Human Review Required":
            interrupt_payload = st.session_state.interrupt_data
            st.markdown(f"**Post Content to Review:**\n```\n{interrupt_payload.get('current_post_content', 'N/A')}\n```")
            if interrupt_payload.get('image_url') and interrupt_payload.get('image_url') != "No image selected.":
                st.image(interrupt_payload.get('image_url'), caption="Selected Image Preview")
            else:
                st.write("No image selected for this post.")
            st.write(f"**Links in post context:** {interrupt_payload.get('links_in_post', [])}")
            st.write(f"**Currently Scheduled:** {interrupt_payload.get('current_schedule_date', 'Not scheduled')}")

            st.markdown("---")
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
if st.session_state.final_graph_output: # This will be set when graph completes successfully
    st.success("Graph Run Completed!")
    st.json(st.session_state.final_graph_output)

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
