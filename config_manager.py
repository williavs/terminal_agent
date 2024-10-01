import json
import os
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.live import Live
from rich.box import DOUBLE
from ascii_art import display_welcome_message

console = Console()

CONFIG_FILE = "config.json"

ASCII_ART = r"""


--      ███        ▄████████    ▄████████   ▄▄▄▄███▄▄▄▄    ▄█  ███▄▄▄▄      ▄████████  ▄█            
--  ▀█████████▄   ███    ███   ███    ███ ▄██▀▀▀███▀▀▀██▄ ███  ███▀▀▀██▄   ███    ███ ███            
--     ▀███▀▀██   ███    █▀    ███    ███ ███   ███   ███ ███▌ ███   ███   ███    ███ ███            
--      ███   ▀  ▄███▄▄▄      ▄███▄▄▄▄██▀ ███   ███   ███ ███▌ ███   ███   ███    ███ ███            
--      ███     ▀▀███▀▀▀     ▀▀███▀▀▀▀▀   ███   ███   ███ ███▌ ███   ███ ▀███████████ ███            
--      ███       ███    █▄  ▀███████████ ███   ███   ███ ███  ███   ███   ███    ███ ███            
--      ███       ███    ███   ███    ███ ███   ███   ███ ███  ███   ███   ███    ███ ███▌    ▄      
--     ▄████▀     ██████████   ███    ███  ▀█   ███   █▀  █▀    ▀█   █▀    ███    █▀  █████▄▄██      
--                             ███    ███                                             ▀              
--               ▄████████    ▄██████▄     ▄████████ ███▄▄▄▄       ███                               
--              ███    ███   ███    ███   ███    ███ ███▀▀▀██▄ ▀█████████▄                           
--              ███    ███   ███    █▀    ███    █▀  ███   ███    ▀███▀▀██                           
--              ███    ███  ▄███         ▄███▄▄▄     ███   ███     ███   ▀                           
--            ▀███████████ ▀▀███ ████▄  ▀▀███▀▀▀     ███   ███     ███                               
--              ███    ███   ███    ███   ███    █▄  ███   ███     ███                               
--              ███    ███   ███    ███   ███    ███ ███   ███     ███                               
--              ███    █▀    ████████▀    ██████████  ▀█   █▀     ▄████▀                             
--                                                                                                   
--               ▄████████    ▄████████     ███     ███    █▄     ▄███████▄                          
--              ███    ███   ███    ███ ▀█████████▄ ███    ███   ███    ███                          
--              ███    █▀    ███    █▀     ▀███▀▀██ ███    ███   ███    ███                          
--              ███         ▄███▄▄▄         ███   ▀ ███    ███   ███    ███                          
--            ▀███████████ ▀▀███▀▀▀         ███     ███    ███ ▀█████████▀                           
--                     ███   ███    █▄      ███     ███    ███   ███                                 
--               ▄█    ███   ███    ███     ███     ███    ███   ███                                 
--             ▄████████▀    ██████████    ▄████▀   ████████▀   ▄████▀                               
--                                                                                                   


By WillyV3
                                                                                                           
"""

SETUP_MODE_TEXT = "   SETUP MODE 🚀"

async def display_welcome_animation():
    welcome_text = Text("Setup your TERMINAL AGENT!", style="bold magenta")
    panel = Panel(welcome_text, expand=False, border_style="cyan")
    
    console.clear()
    # console.print(ASCII_ART)
    
    console.print(ASCII_ART)
    console.print(panel, justify="center")
    await asyncio.sleep(2)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

async def setup_menu():
    config = load_config()
    
    await display_welcome_animation()
    
    console.print("[bold]Let's configure your TERMINAL AGENT![/bold]")
    
    # Choose LLM provider
    llm_provider = Prompt.ask(
        "Type 'ant' to setup Anthropic models or 'gpt' to setup OpenAI Models",
        choices=["ant", "gpt"],
        default="gpt"
    )
    config["llm_provider"] = "anthropic" if llm_provider == "ant" else "openai"
    
    # Input API key
    api_key = Prompt.ask(f"Enter your {config['llm_provider'].upper()} API key", password=True)
    config[f"{config['llm_provider']}_api_key"] = api_key
    
    # Choose model
    if config["llm_provider"] == "openai":
        model = Prompt.ask(
            "Choose OpenAI model",
            choices=["gpt-4o", "gpt-4o-mini"],
            default="gpt-4o-mini"
        )
    else:  # anthropic
        model = Prompt.ask(
            "Choose Anthropic model",
            choices=["claude-3-5-sonnet-20240620"],
            default="claude-3-5-sonnet-20240620"
        )
    config["model"] = model
    
    save_config(config)
    console.print("[green]Configuration saved successfully![/green]")
    
    welcome_text = Text("AI Assistant is ready to chat!", style="bold green")
    panel = Panel(welcome_text, expand=False, border_style="cyan")
    console.print(panel, justify="center")
    await asyncio.sleep(2)

async def get_llm_config():
    config = load_config()
    if not config or Confirm.ask("Do you want to reconfigure the AI assistant?"):
        await setup_menu()
        config = load_config()
    return config

if __name__ == "__main__":
    asyncio.run(setup_menu())