from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich.live import Live
import time
from rich import box
from rich.align import Align
from rich.markdown import Markdown
from rich.console import Group
from rich.columns import Columns
import random
import math

WELCOME_ASCII_ART = r"""                          


--      ███        ▄████████    ▄████████   ▄▄▄▄███▄▄▄▄    ▄█  ███▄▄▄▄      ▄████████  ▄█            
--  ▀█████████▄   ███    ███   ███    ███ ▄██▀▀▀███▀▀▀██▄ ███  ███▀▀▀██▄   ███    ███ ███            
--     ▀███▀▀██   ███    █▀    ███    ███ ███   ███   ███ ███▌ ███   ███   ███    ███ ███            
--      ███   ▀  ▄███▄▄▄      ▄███▄▄▄▄██▀ ███   ███   ███ ███▌ ███   ███   ███    ███ ███            
--      ███     ▀▀███▀▀▀     ▀▀███▀▀▀▀▀   ███   ███   ███ ███▌ ███   ███ ▀███████████ ███            
--      ███       ███    █▄  ▀███████████ ███   ███   ███ ███  ███   ███   ███    ███ ███            
--      ███       ███    ███   ███    ███ ███   ███   ███ ███  ███   ███   ███    ███ ███▌    ▄      
--     ▄████▀     ██████████   ███    ███  ▀█   ███   █▀  █▀    ▀█   █▀    ███    █▀  █████▄▄██      
--                                                                  ▀              
--               ▄████████    ▄██████▄     ▄████████ ███▄▄▄▄       ███                               
--              ███    ███   ███    ███   ███    ███ ███▀▀▀██▄ ▀█████████▄                           
--              ███    ███   ███    █▀    ███    █▀  ███   ███    ▀███▀▀██                           
--              ███    ███  ▄███         ▄███▄▄▄     ███   ███     ███   ▀                           
--            ▀███████████ ▀▀███ ████▄  ▀▀███▀▀▀    ███   ███     ███                               
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

--                                                                       
                                                
"""

WELCOME_MESSAGE = """
# Welcome to WillyV's Terminal Agent (V1) 🚀

https://www.linkedin.com/in/willyv3/

Type your questions, and let's explore the future together!
Type 'quit' or 'Ctrl+C' to exit the chat.
"""

def interpolate_color(start, end, factor: float):
    return f"#{int(start[0] + (end[0] - start[0]) * factor):02x}" \
           f"{int(start[1] + (end[1] - start[1]) * factor):02x}" \
           f"{int(start[2] + (end[2] - start[2]) * factor):02x}"

def rainbow_color(t):
    r = int(abs(math.sin(2 * math.pi * t / 100)) * 127 + 128)
    g = int(abs(math.sin(2 * math.pi * t / 100 + 2 * math.pi / 3)) * 127 + 128)
    b = int(abs(math.sin(2 * math.pi * t / 100 + 4 * math.pi / 3)) * 127 + 128)
    return f"#{r:02x}{g:02x}{b:02x}"

def animate_matrix(text):
    lines = text.split('\n')
    for i in range(len(lines[0])):
        yield Text('\n'.join(line[:i+1].ljust(len(line)) for line in lines), style="bold green")
        time.sleep(0.005)  # Reduced from 0.01 to speed up the matrix effect

def animate_glow():
    colors = [
        (255, 0, 0),    # red
        (255, 127, 0),  # orange
        (255, 255, 0),  # yellow
        (0, 255, 0),    # green
        (0, 0, 255),    # blue
        (75, 0, 130),   # indigo
        (143, 0, 255),  # violet
    ]
    
    ascii_lines = WELCOME_ASCII_ART.split('\n')
    max_line_length = max(len(line) for line in ascii_lines)
    
    for i in range(100):  # Increased for a longer animation
        gradient_text = ""
        white_glow_pos = int((math.sin(i * 0.1) + 1) * max_line_length / 2)
        
        for y, line in enumerate(ascii_lines):
            for x, char in enumerate(line.ljust(max_line_length)):
                if char.strip():
                    color_index = int((x + i) % len(colors))
                    next_color_index = (color_index + 1) % len(colors)
                    factor = (x + i) % 1.0
                    color = interpolate_color(colors[color_index], colors[next_color_index], factor)
                    
                    # Add white glow effect
                    distance = abs(x - white_glow_pos)
                    if distance < 5:
                        glow_factor = 1 - (distance / 5)
                        color = interpolate_color(hex_to_rgb(color), (255, 255, 255), glow_factor)
                    
                    gradient_text += f"[{color}]{char}[/]"
                else:
                    gradient_text += char
            gradient_text += "\n"
        
        styled_text = Text.from_markup(gradient_text.strip())
        
        yield styled_text
        time.sleep(0.05)  # Adjusted for smooth animation

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def animate_rainbow():
    for i in range(30):  # Increased from 100 to 200 to extend the rainbow animation
        color = rainbow_color(i)
        yield Text(WELCOME_ASCII_ART, style=Style(color=color, bold=True))

def animate_typing(text, speed=0.01):
    for i in range(len(text) + 1):
        yield Text(text[:i], style="bold white")
        time.sleep(speed)

def display_welcome_message():
    console = Console()

    welcome_text = Markdown(WELCOME_MESSAGE)

    with Live(console=console, screen=True, refresh_per_second=30) as live:
        # Gradient glow effect (starts immediately)
        for frame in animate_glow():
            panel = Panel(
                Group(
                    frame,
                    Text("\n")
                ),
                box=box.ROUNDED,
                border_style="bold cyan",
                title="Terminal Agent",
                title_align="center",
            )
            live.update(panel)

        # Typing effect for welcome message
        for typed_text in animate_typing(WELCOME_MESSAGE, speed=0.01):
            panel = Panel(
                Group(
                    Text(WELCOME_ASCII_ART, style="green"),
                    Text("\n"),
                    typed_text
                ),
                box=box.ROUNDED,
                border_style="bold cyan",
                title="Terminal Agent",
                title_align="center",
            )
            live.update(panel)

    # Keep the final frame visible
    console.print(panel)