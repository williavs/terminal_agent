import json
from langchain.prompts import ChatPromptTemplate
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from llm_components.shared import sync_structured_search, AgentState

# Initialize Rich console for better formatting
console = Console()

def search_node(state: AgentState, llm) -> AgentState:
    """Perform a web search based on the search query."""
    if state["search_count"] < 5:
        search_query = state["search_query"] if state["search_query"] else state["messages"][-1].content
        
        # Double-check relevance
        relevance_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI assistant tasked with ensuring search queries are relevant to the user's question and conversation context."),
            ("human", """User's question: {last_message}
Conversation context: {conversation_history}
Proposed search query: {search_query}

Is this search query relevant and specific to the user's question and conversation context? If not, provide a more relevant query. todays date is September 30, 2024 Respond with either:
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
    return {**state, "decision": "respond"}  # Force respond if max searches reached

def analyze_node(state: AgentState, llm) -> AgentState:
    """Analyze the search results."""
    analysis_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant tasked with analyzing search results. Provide a concise summary of the key points. If the information is insufficient or irrelevant, clearly state so and explain why. If you encounter any errors or inconsistencies in the search results, report them explicitly."""),
        ("human", "Analyze the following search results:\n{search_results}")
    ])
    analysis_chain = analysis_prompt | llm
    analysis = analysis_chain.invoke({"search_results": json.dumps(state["search_results"])})
    console.print(Panel(Markdown(analysis.content), title="Analysis", expand=False))
    return {**state, "analysis": analysis.content, "decision": "decide"}  # Set next decision to 'decide'

def decide_node(state: AgentState, llm) -> AgentState:
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

Your response should be in one of these formats:
1. 'SEARCH: [specific search query]' if more information is needed.
2. 'RESPOND' if the information is sufficient to answer the question accurately.
         
          If we need to search, what specific information should we look for? Ensure the search query is directly relevant to the user's question and the conversation context.""")
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

def respond_node(state: AgentState, llm) -> AgentState:
    """Generate a response based on the analysis, conversation history, and memory."""
    response_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant tasked with providing precise and relevant information based on web search results and past interactions. Your responses should be:
1. Directly relevant to the user's question
2. Concise yet comprehensive
3. Well-structured and easy to read
4. Backed by the information from the search results and past interactions

When providing information:
- Always provide up-to-date info. Today is September 30, 2024.
- If you encounter any errors or inconsistencies in the search results or analysis, report them explicitly to the user.
- If you're unsure about any information or if the search results are inadequate, state so clearly.
- Avoid mixing unrelated topics unless they are directly relevant to the user's query.

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

def initial_response_node(state: AgentState, llm) -> AgentState:
    """Attempt to answer the question without searching."""
    initial_response_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant with broad knowledge. Attempt to answer the user's question based on your existing knowledge. If you can confidently answer the question, do so. If you need more information or are unsure, admit that you need to search for more details.

Your response should be in one of these formats:
1. 'ANSWER: [your confident answer]' if you can answer without additional search.
2. 'SEARCH_NEEDED' if you need more information to provide an accurate answer.

Today's date is September 30, 2024."""),
        ("human", "{question}")
    ])
    initial_response_chain = initial_response_prompt | llm
    response = initial_response_chain.invoke({"question": state["messages"][-1].content})
    
    response_content = response.content.strip()
    if response_content.startswith("ANSWER:"):
        answer = response_content[7:].strip()
        console.print(Panel(Markdown(answer), title="Initial Response", expand=False))
        return {**state, "messages": [*state["messages"], AIMessage(content=answer)], "decision": "respond"}
    else:
        console.print("[bold yellow]Initial response: More information needed. Proceeding to search.[/bold yellow]")
        return {**state, "decision": "search"}