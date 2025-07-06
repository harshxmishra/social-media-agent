from typing import Dict, Any
from ...state import GeneratePostState # Corrected relative import
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
import os

async def generate_content_report_node(state: GeneratePostState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a content report using an LLM to summarize fetched pageContents.
    """
    print(f"DEBUG: Node: generate_content_report_node for links: {state.links}")
    if not state.pageContents:
        print("DEBUG: No page contents to generate a report from.")
        return {"report": "No content was available to generate a report."}

    # Ensure API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found for generate_content_report_node.")
        return {"report": "Error: LLM API key not configured."}

    try:
        # Initialize LLM - consider making this a shared client if used in many nodes
        # For simplicity, initializing here. Model name can be configured.
        llm = ChatAnthropic(model="claude-3-haiku-20240307", api_key=api_key, temperature=0.3)

        concatenated_content = "\n\n".join(state.pageContents)
        # Truncate content if it's excessively long to avoid high token costs / API limits for summary
        max_content_length = 15000 # Example limit, adjust as needed
        if len(concatenated_content) > max_content_length:
            concatenated_content = concatenated_content[:max_content_length] + "\n... (content truncated)"

        prompt_text = (
            f"Please generate a concise, factual report summarizing the key information from the following web content. "
            f"The report should be suitable for informing the creation of a social media post. "
            f"Focus on the main topics, any significant outcomes, or unique aspects mentioned.\n\n"
            f"Web Content:\n\"\"\"\n{concatenated_content}\n\"\"\"\n\n"
            f"Concise Report:"
        )

        messages = [HumanMessage(content=prompt_text)]

        print(f"DEBUG: Calling LLM for content report generation. Content length: {len(concatenated_content)}")
        response = await llm.ainvoke(messages)
        report_content = response.content

        print(f"DEBUG: LLM generated report: {report_content[:150]}...")
        return {"report": report_content}

    except Exception as e:
        print(f"ERROR: LLM call failed in generate_content_report_node: {e}")
        return {"report": f"Error during report generation: {str(e)}"}
