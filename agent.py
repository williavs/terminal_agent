import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SearxSearchWrapper
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.tools import StructuredTool
from langchain.prompts import ChatPromptTemplate
import json
import asyncio
from pydantic import BaseModel, Field
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.prompt import Prompt
from rich.syntax import Syntax
from typing import TypedDict, Annotated, Sequence, List, Dict, Any
from rich.box import HEAVY
from rich.text import Text
from rich.style import Style

# Load environment variables from .env file
load_dotenv()

# Initialize Rich console for better formatting
console = Console()

# Initialize OpenAI LLM
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
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

# Create a StructuredTool for the search
search_tool = StructuredTool(
    name="web_search",
    description="Search the web for information. Input should be a search query string.",
    func=sync_structured_search,
    args_schema=SearchInput,
)

# Update AgentState to include memory
class AgentState(TypedDict):
    messages: Annotated[Sequence[SystemMessage | HumanMessage | AIMessage], "The messages in the conversation"]
    search_results: Annotated[List[str], "The results from the web searches"]
    analysis: Annotated[str, "The analysis of the search results"]
    search_count: Annotated[int, "The number of searches performed"]
    decision: Annotated[str, "The decision to search or respond"]
    search_query: Annotated[str, "The query for the next search"]
    memory: Annotated[Dict[str, Any], "The memory of past interactions"]

# Define the nodes
def search_node(state: AgentState) -> AgentState:
    """Perform a web search based on the search query."""
    if state["search_count"] < 5:
        search_query = state["search_query"] if state["search_query"] else state["messages"][-1].content
        
        # Double-check relevance
        relevance_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI assistant tasked with ensuring search queries are relevant to the user's question and conversation context."),
            ("human", """User's question: {last_message}
Conversation context: {conversation_history}
Proposed search query: {search_query}

Is this search query relevant and specific to the user's question and conversation context? If not, provide a more relevant query. Respond with either:
1. 'RELEVANT: [original query]' if the query is good.
2. 'UPDATED: [new query]' if you have a better, more relevant query.""")
        ])
        relevance_chain = relevance_prompt | llm
        relevance_check = relevance_chain.invoke({
            "last_message": state["messages"][-1].content,
            "conversation_history": "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in state["memory"].get("messages", [])]),
            "search_query": search_query
        })
        
        relevance_content = relevance_check.content.strip()
        if relevance_content.startswith("UPDATED:"):
            search_query = relevance_content[8:].strip()
            console.print(f"[bold yellow]Updated search query:[/bold yellow] {search_query}")
        
        search_results = sync_structured_search(search_query)
        console.print(Panel(Syntax(search_results, "json", theme="monokai", line_numbers=True), title=f"Search Results (Attempt {state['search_count'] + 1})", expand=False))
        return {
            **state,
            "search_results": state["search_results"] + [search_results],
            "search_count": state["search_count"] + 1,
            "search_query": ""  # Reset the search query after using it
        }
    return state

def analyze_node(state: AgentState) -> AgentState:
    """Analyze the search results."""
    analysis_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant tasked with analyzing search results. Provide a concise summary of the key points. If the information is insufficient, clearly state what specific additional details are needed."),
        ("human", "Analyze the following search results:\n{search_results}")
    ])
    analysis_chain = analysis_prompt | llm
    analysis = analysis_chain.invoke({"search_results": json.dumps(state["search_results"])})
    console.print(Panel(Markdown(analysis.content), title="Analysis", expand=False))
    return {**state, "analysis": analysis.content}

def decide_node(state: AgentState) -> AgentState:
    """Decide whether to search again or proceed to respond."""
    decision_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant tasked with deciding whether the current information is sufficient to answer the user's question or if more searching is needed. Consider the conversation history and previous answers when making your decision.

If more searching is needed, formulate a specific and relevant search query based on the user's question and the current context of the conversation. The search query should be directly related to finding the requested information.

Your response should be in one of these formats:
1. 'SEARCH: [specific search query]' if more information is needed.
2. 'RESPOND' if the information is sufficient to answer the question accurately."""),
        ("human", """Based on this analysis: {analysis}

And the user's question: {last_message}

Consider the search count: {search_count}

Previous conversation:
{conversation_history}

Should we search for more information or proceed to respond? If we need to search, what specific information should we look for? Ensure the search query is directly relevant to the user's question and the conversation context.""")
    ])
    decision_chain = decision_prompt | llm
    last_human_message = next((msg for msg in reversed(state["messages"]) if isinstance(msg, HumanMessage)), None)
    
    conversation_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in state["memory"].get("messages", [])])
    
    decision = decision_chain.invoke({
        "analysis": state["analysis"],
        "last_message": last_human_message.content if last_human_message else "No message found.",
        "search_count": state["search_count"],
        "conversation_history": conversation_history
    })
    decision_content = decision.content.strip().upper()
    if decision_content.startswith("SEARCH:") and state["search_count"] < 5:
        new_query = decision_content[7:].strip()
        console.print(f"[bold cyan]Searching for:[/bold cyan] {new_query}")
        return {**state, "decision": "search", "search_query": new_query}
    else:
        return {**state, "decision": "respond"}

def respond_node(state: AgentState) -> AgentState:
    """Generate a response based on the analysis, conversation history, and memory."""
    response_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant tasked with providing precise and relevant information based on web search results and past interactions. Your responses should be:
1. Directly relevant to the user's question
2. Concise yet comprehensive
3. Well-structured and easy to read
4. Backed by the information from the search results and past interactions

When providing information about ticket prices or event details:
- List prices from lowest to highest
- Include direct links to ticket purchasing pages when available
- Mention any discounts or special offers
- Specify the source of the information (e.g., "According to TicketCity,...")

If the information is not available or unclear, state so explicitly.

Consider the following memory of past interactions when formulating your response:
{memory}

Enclose your response between <response> tags."""),
        ("human", """Based on this analysis: 
<analysis>
{analysis}
</analysis>

And considering the conversation history and memory:
{conversation_history}

Respond to the user's last message: 
<user_message>
{last_message}
</user_message>

Provide your response below:""")
    ])
    response_chain = response_prompt | llm
    last_human_message = next((msg for msg in reversed(state["messages"]) if isinstance(msg, HumanMessage)), None)
    
    conversation_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in state["memory"].get("messages", [])])
    
    response = response_chain.invoke({
        "analysis": state["analysis"],
        "memory": json.dumps(state["memory"]),
        "conversation_history": conversation_history,
        "last_message": last_human_message.content if last_human_message else "No message found."
    })
    
    import re
    response_content = re.search(r'<response>(.*?)</response>', response.content, re.DOTALL)
    if response_content:
        formatted_response = response_content.group(1).strip()
    else:
        formatted_response = response.content.strip()
    
    return {**state, "messages": [*state["messages"], AIMessage(content=formatted_response)]}

# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("search", search_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("decide", decide_node)
workflow.add_node("respond", respond_node)

# Add edges
workflow.add_edge("search", "analyze")
workflow.add_edge("analyze", "decide")
workflow.add_conditional_edges(
    "decide",
    lambda x: x["decision"],
    {
        "search": "search",
        "respond": "respond"
    }
)
workflow.add_edge("respond", END)

# Set entry point
workflow.set_entry_point("search")

# Compile the graph
graph = workflow.compile()

def display_welcome_message():
    welcome_message = Panel(
        "[bold blue]Welcome to the AI Assistant Terminal Chat![/bold blue]\n"
        "Type your questions and I'll do my best to answer.\n"
        "Type 'quit' to exit the chat.",
        expand=False,
        border_style="bold",
        title="AI Assistant",
        title_align="center"
    )
    console.print(welcome_message)

def get_user_input():
    return Prompt.ask("[bold green]You")

def display_thinking_animation():
    with Live(console=console, refresh_per_second=4) as live:
        for i in range(3):
            live.update(Spinner("dots", text="Processing..."))
            time.sleep(0.5)

# Update the main function to use memory
def main():
    display_welcome_message()
    
    messages = [SystemMessage(content="You are an AI assistant with access to web search capabilities and memory of past interactions.")]
    
    memory_state = {"messages": []}
    
    while True:
        try:
            user_input = get_user_input()
            
            if user_input.lower() == 'quit':
                console.print("[bold blue]Goodbye! Thanks for chatting.[/bold blue]")
                break
            
            messages.append(HumanMessage(content=user_input))
            memory_state["messages"].append({"role": "user", "content": user_input})
            
            display_thinking_animation()
            
            state = {
                "messages": messages,
                "search_results": [],
                "analysis": "",
                "search_count": 0,
                "decision": "",
                "search_query": user_input,
                "memory": memory_state
            }
            
            while True:
                state = graph.invoke(state)
                if END in state or state["decision"] == "respond":
                    break
                if state["search_count"] >= 5:
                    console.print("[bold yellow]Maximum number of searches reached. Proceeding with available information.[/bold yellow]")
                    break
            
            ai_response = state["messages"][-1].content
            memory_state["messages"].append({"role": "assistant", "content": ai_response})
            
            # Create a colorful and branded panel for the final response
            header = "[bold magenta]WillyV's[/bold magenta] [bold cyan]AI Assistant[/bold cyan]"
            footer = "[italic]Powered by GPT-4o & SearxNG[/italic]\n[bold green]Created by William Van Sickle[/bold green]"
            
            final_response_panel = Panel(
                Markdown(ai_response),
                title=header,
                subtitle=footer,
                expand=False,
                border_style="cyan",
                box=HEAVY,
                padding=(1, 1),
                style="on black"
            )
            
            console.print("\n")  # Add some space before the final response
            console.print(final_response_panel)
            console.print("\n")  # Add some space after the final response
            
            messages = state["messages"]
            
        except Exception as e:
            console.print(Panel(f"An error occurred: {str(e)}", title="[bold red]Error[/bold red]", border_style="red"))

if __name__ == "__main__":
    main()