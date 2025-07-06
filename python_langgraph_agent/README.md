# Python Social Media Agent with LangGraph and Streamlit

## Overview

This project is a Python-based Social Media Agent that processes URLs, generates engaging social media posts (primarily for Twitter/X and LinkedIn), and incorporates a Human-in-the-Loop (HITL) review process. It leverages the LangGraph library for building robust, stateful agentic workflows and uses Streamlit for the user interface.

This is a conversion and enhancement of an original Typescript-based project.

## Features

*   **URL Processing:** Ingests one or more URLs as input.
*   **Content Scraping:** Fetches and extracts relevant content from the provided URLs (currently using Firecrawl for general web pages).
*   **Content Summarization:** Generates a concise report from the scraped content using an LLM (e.g., Anthropic Claude).
*   **Social Media Post Generation:** Creates draft posts suitable for platforms like Twitter/X and LinkedIn based on the generated report, using an LLM.
*   **Post Refinement:**
    *   **Condensation:** Automatically shortens posts if they exceed platform character limits.
    *   **Rewrite:** Allows users to request post rewrites based on their feedback.
    *   **URL Splitting:** Can rewrite a post to move a primary URL into a follow-up reply/comment (useful for Twitter).
*   **Human-in-the-Loop (HITL) Review:** Presents generated posts to the user for review via a Streamlit interface. Users can:
    *   Approve and schedule the post.
    *   Request edits with feedback.
    *   Update the scheduled date/time.
    *   Discard the post.
*   **Image Handling (Placeholder):** Includes graph components for finding, validating, and selecting images for posts (currently with placeholder logic).
*   **Authentication Management:**
    *   Supports basic token-based authentication for social media platforms.
    *   Integrates with ArcadeAI for a streamlined OAuth-based authorization flow (if configured).
    *   Handles auth interruptions gracefully within the Streamlit UI, prompting the user to authorize when needed.
*   **Streamlit UI:** Provides a user-friendly web interface for:
    *   Submitting URLs for processing.
    *   Configuring generation parameters (e.g., text-only mode).
    *   Interacting with the HITL review and authorization steps.
    *   Viewing execution logs and final outputs.
*   **Checkpointing:** Uses LangGraph's checkpointing (`MemorySaver`) to maintain graph state across interactions, enabling resumable flows.

## Directory Structure

```
python_langgraph_agent/
├── app/
│   ├── __init__.py
│   ├── clients/                # Client wrappers for external services (Arcade, Firecrawl, Supabase, social media APIs)
│   │   ├── __init__.py
│   │   ├── arcade_manager_wrapper.py
│   │   ├── firecrawl_client.py
│   │   ├── github_client.py (stub)
│   │   ├── linkedin_client.py (stub)
│   │   ├── slack_client.py (stub)
│   │   ├── supabase_client.py
│   │   └── twitter_client.py (stub)
│   ├── nodes/                  # Individual processing steps (nodes) for the LangGraph agent
│   │   ├── __init__.py
│   │   ├── auth_socials.py
│   │   ├── content_generation_nodes/
│   │   ├── find_images_nodes/ (placeholders)
│   │   ├── interaction_nodes/ (HITL, scheduling)
│   │   └── verification_nodes/ (placeholders, except general content)
│   ├── subgraphs/              # Smaller, reusable LangGraphs
│   │   ├── __init__.py
│   │   ├── find_images_graph.py (placeholder logic)
│   │   └── verify_links_graph.py (processes first link, placeholder verification nodes)
│   ├── utils.py                # Utility functions
│   ├── state.py                # Pydantic models for the main graph state (GeneratePostState)
│   ├── models.py               # Other Pydantic data models
│   └── generate_post_flow.py   # Main LangGraph definition for the "generate_post" agent
├── .env.example                # Example environment variables file
├── pyproject.toml              # Project dependencies and metadata (Poetry)
├── README.md                   # This file
└── streamlit_app.py            # Main Streamlit application file
```

## Setup Instructions

### Prerequisites

*   Python 3.10+
*   Poetry (for dependency management and running the project)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>/python_langgraph_agent
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```

### Environment Variables

1.  Navigate to the `python_langgraph_agent` directory.
2.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
3.  Edit the `.env` file and fill in the required API keys and configuration details. See `.env.example` for the full list of variables.

    **Key Required Variables:**
    *   `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`: For Large Language Model access. Anthropic is used by default in current nodes.
    *   `FIRECRAWL_API_KEY`: For web content scraping.

    **Conditional/Social Media Variables:**
    *   `USE_ARCADE_AUTH`: Set to `true` to use ArcadeAI for social media authentication, `false` for basic token auth.
    *   If `USE_ARCADE_AUTH=true`:
        *   `ARCADE_API_KEY`: Required.
        *   `LINKEDIN_USER_ID`, `TWITTER_USER_ID`: Your application's internal identifiers for the user on these platforms, passed to Arcade.
    *   If `USE_ARCADE_AUTH=false` (for basic auth, requires manual token setup):
        *   `TWITTER_API_KEY`, `TWITTER_API_KEY_SECRET`
        *   `TWITTER_USER_TOKEN`, `TWITTER_USER_TOKEN_SECRET` (User context OAuth 1.0a tokens)
        *   `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`
        *   `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN` (User's access token and URN)
    *   For LinkedIn Organization Posts:
        *   `POST_TO_LINKEDIN_ORGANIZATION`: Set to `true` to enable posting as an organization.
        *   `LINKEDIN_ORGANIZATION_ID`: The ID or URN of the LinkedIn Organization.
    *   Image Storage (Optional, but image features will be limited):
        *   `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`: For storing images selected for posts.
    *   Optional for specific verification nodes (if fully implemented):
        *   `GITHUB_TOKEN`
        *   `SLACK_BOT_TOKEN`, `SLACK_TEST_CHANNEL_ID`

## Running the Application

1.  Ensure you are in the `python_langgraph_agent` directory.
2.  Make sure your Poetry virtual environment is active or use `poetry run`.
3.  Run the Streamlit application:
    ```bash
    poetry run streamlit run streamlit_app.py
    ```
4.  Open the URL provided by Streamlit (usually `http://localhost:8501`) in your web browser.

## How to Use

1.  **Open the Streamlit App:** Navigate to the app in your browser.
2.  **Configure API Keys:** Ensure your `.env` file is correctly set up with necessary API keys. The sidebar will show warnings for missing critical keys.
3.  **Input URLs:** Enter one or more URLs (one per line) into the text area that you want to generate posts for.
4.  **Set Options:**
    *   **Text-Only Mode:** Check if you don't want image processing or specific YouTube handling.
    *   **Post to LinkedIn Organization:** Check if you intend for posts to go to a LinkedIn company page (requires `LINKEDIN_ORGANIZATION_ID` in `.env`).
    *   **Arcade User ID:** If using Arcade for authentication (`USE_ARCADE_AUTH=true`), provide a unique identifier for the current user (e.g., their email or a UUID). This is used by Arcade to manage their authorizations.
5.  **Generate Post:** Click the "🚀 Generate Post" button.
6.  **Monitor Execution:** The "Execution Log" expander will show the progress of the agent through its various steps.
7.  **Handle Interrupts:**
    *   **Authorization:** If the agent needs to access a social media account (e.g., LinkedIn, Twitter via Arcade) and isn't authorized, an interrupt will occur. The UI will display an authorization URL or instructions. Follow them, then click "I have authorized / Retry Authorization" in the Streamlit app to continue.
    *   **Human Review:** Once a draft post is generated, the agent will interrupt for your review. The UI will display the draft post, any selected image (placeholder for now), and available actions:
        *   **Approve and Schedule:** (Placeholder - logs intent to schedule)
        *   **Request Rewrite:** Provide feedback in the text area and click.
        *   **Rewrite (Split URL to Reply):** (Placeholder - attempts to move first URL to a reply)
        *   **Update Schedule Date:** Provide a new date/time string (e.g., "tomorrow 3pm", "2024-12-31", "p1") and click.
        *   **Discard Post:** Ends the process for this post.
8.  **View Final Output:** If the graph completes successfully (e.g., after scheduling or discarding), the final generated content will be displayed.

## Technical Overview

*   **LangGraph:** The core agent logic is built as a stateful graph using `langgraph`. The main graph definition is in `app/generate_post_flow.py`. It defines the states, nodes (processing steps), and conditional edges that control the flow.
*   **Streamlit:** Provides the web UI for interaction, input, and displaying results. `streamlit_app.py` manages the UI and calls the LangGraph agent.
*   **Pydantic:** Used for defining the structure of the graph state (`app/state.py`) and other data models (`app/models.py`).
*   **Asynchronous Operations:** Graph execution and some client interactions are asynchronous (`async`/`await`). Streamlit's integration with `asyncio` is used.

## Current Status & Limitations

*   **Core Flow Implemented:** The main graph structure for generating posts, including HITL review and basic auth interrupt handling, is in place.
*   **Placeholder Node Logic:** Many nodes, especially those involving actual social media API calls (posting, advanced verification), image processing, and complex LLM prompting, currently have placeholder or simplified logic.
    *   LLM calls for report generation, post drafting, condensation, and rewriting are basic implementations.
    *   `verify_general_content` uses Firecrawl. Other verification nodes are mocks.
    *   Image selection and actual posting/scheduling are placeholders.
*   **Client Stubs:** Client wrappers for Twitter, LinkedIn, GitHub, Slack are mostly stubs and require full implementation for live interaction.
*   **Error Handling:** Basic error handling is in place, but can be made more granular.
*   **Configuration:** Relies on environment variables. More complex configuration management might be needed for advanced use cases.

This project provides a solid foundation for a Python-based social media agent. Further development will focus on fully implementing the placeholder logic and client integrations.
