import os
import time
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.prompt import Prompt
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import asyncio
from ascii_art import display_welcome_message
from config_manager import get_llm_config
from llm_components.shared import get_llm, sync_structured_search, AgentState
from llm_components.graph_nodes import search_node, analyze_node, decide_node, respond_node, initial_response_node

# Load environment variables from .env file
load_dotenv()

# Initialize Rich console for better formatting
console = Console()

async def initialize_config():
    return await get_llm_config()

# Get LLM configuration
config = asyncio.run(initialize_config())

# Initialize LLM
llm = get_llm(config)

# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("initial_response", lambda state: initial_response_node(state, llm))
workflow.add_node("search", lambda state: search_node(state, llm))
workflow.add_node("analyze", lambda state: analyze_node(state, llm))
workflow.add_node("decide", lambda state: decide_node(state, llm))
workflow.add_node("respond", lambda state: respond_node(state, llm))

# Add edges
workflow.add_conditional_edges(
    "initial_response",
    lambda x: x["decision"],
    {
        "search": "search",
        "respond": "respond"
    }
)
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
workflow.set_entry_point("initial_response")

# Compile the graph
graph = workflow.compile()

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
            
            # Reset state for new interaction
            messages = [SystemMessage(content="You are an AI assistant with access to web search capabilities and memory of past interactions.")]
            messages.append(HumanMessage(content=user_input))
            
            memory_state["messages"].append({"role": "user", "content": user_input})
            
            display_thinking_animation()
            
            state = {
                "messages": messages,
                "search_results": [],
                "analysis": "",
                "search_count": 0,
                "decision": "initial_response",  # Start with initial response
                "search_query": user_input,
                "memory": memory_state
            }
            
            max_iterations = 10
            iteration_count = 0
            
            while iteration_count < max_iterations:
                previous_state = state.copy()
                
                state = graph.invoke(state)
                
                iteration_count += 1
                
                console.print(f"Iteration {iteration_count}: Decision = {state['decision']}, Search Count = {state['search_count']}, Query = '{state['search_query']}'")
                
                if END in state or state["decision"] == "respond":
                    break
                
                if state == previous_state:
                    console.print("[bold yellow]State unchanged. Breaking loop.[/bold yellow]")
                    break
            
            # ... (rest of the code remains the same)
            
            ai_response = state["messages"][-1].content
            memory_state["messages"].append({"role": "assistant", "content": ai_response})
            
            # Add error checking for the AI response
            if "error" in ai_response.lower() or "insufficient information" in ai_response.lower():
                console.print("[bold yellow]Warning: The AI encountered issues while processing your request. The response may be incomplete or inaccurate.[/bold yellow]")
            
            # Create a simple panel for the final response
            response_panel = Panel(
                Markdown(ai_response),
                title=f"AI Assistant Response ({config['llm_provider'].capitalize()} - {config['model']})",
                expand=False,
                border_style="cyan",
                padding=(1, 1),
                style="on black"
            )
            
            console.print("\n")  # Add some space before the final response
            console.print(response_panel)
            console.print("\n")  # Add some space after the final response
            
            # Reset the state for the next iteration
            messages = [SystemMessage(content="You are an AI assistant with access to web search capabilities and memory of past interactions.")]
            messages.extend(state["messages"][-2:])  # Keep only the last user message and AI response
            
        except Exception as e:
            console.print(Panel(f"An error occurred: {str(e)}", title="[bold red]Error[/bold red]", border_style="red"))
            console.print("[bold yellow]Resetting conversation due to error. Please try your query again.[/bold yellow]")
            messages = [SystemMessage(content="You are an AI assistant with access to web search capabilities and memory of past interactions.")]
            memory_state = {"messages": []}

if __name__ == "__main__":
    main()