from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.utilities import SearxSearchWrapper
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, Sequence, List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import asyncio
import json


# Initialize LLM
def get_llm(config):
    if config["llm_provider"] == "openai":
        return ChatOpenAI(
            openai_api_key=config["openai_api_key"],
            model=config["model"]
        )
    else:  # anthropic
        return ChatAnthropic(
            anthropic_api_key=config["anthropic_api_key"],
            model=config["model"]
        )

# Set up the SearxNG wrapper
searx_host = "http://localhost:8080"
searx_wrapper = SearxSearchWrapper(
    searx_host=searx_host,
    engines=["google", "bing", "duckduckgo"]
)

# Define SearchInput model
class SearchInput(BaseModel):
    query: str = Field(..., description="The search query string")

# Define structured search function
async def structured_search(query: str) -> str:
    """Perform a web search with a query string."""
    try:
        result = await searx_wrapper.aresults(query, num_results=5)
        if result:
            return json.dumps(result)
        else:
            return json.dumps([{"error": "No results found"}])
    except Exception as e:
        return json.dumps([{"error": f"Search error: {str(e)}"}])

# Create a synchronous wrapper for the asynchronous search function
def sync_structured_search(query: str) -> str:
    return asyncio.run(structured_search(query))

# Define AgentState
class AgentState(TypedDict):
    messages: Annotated[Sequence[SystemMessage | HumanMessage | AIMessage], "The messages in the conversation"]
    search_results: Annotated[List[str], "The results from the web searches"]
    analysis: Annotated[str, "The analysis of the search results"]
    search_count: Annotated[int, "The number of searches performed"]
    decision: Annotated[str, "The decision to search or respond"]
    search_query: Annotated[str, "The query for the next search"]
    memory: Annotated[Dict[str, Any], "The memory of past interactions"]