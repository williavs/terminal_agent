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
            ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗                    
            ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║                    
               ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║                    
               ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║                    
               ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗               
               ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝               
                                                                                            
 █████╗  ██████╗ ███████╗███╗   ██╗████████╗      ██╗   ██╗       ██████╗ ███╗   ██╗███████╗
██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝      ██║   ██║      ██╔═══██╗████╗  ██║██╔════╝
███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   █████╗██║   ██║█████╗██║   ██║██╔██╗ ██║█████╗  
██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ╚════╝╚██╗ ██╔╝╚════╝██║   ██║██║╚██╗██║██╔══╝  
██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║          ╚████╔╝       ╚██████╔╝██║ ╚████║███████╗
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝           ╚═══╝         ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                            
                                                                                                                                                                                                                
"""

WELCOME_MESSAGE = """
# Welcome to WillyV's Terminal Agent (V1) 🚀

**Willy John (WJVSIII) VanSickle III**
Paradigm Shifter | AI Enthusiast | Product Innovator | 

CURRENTLY RUNNING ON: GPT-4o
(WIP: Claude 3.5 Sonnet, Local M)

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
    base_color = (0, 255, 255)  # cyan
    glow_color = (255, 255, 255)  # white
    
    for i in range(100):
        factor = abs((i % 50) - 25) / 25.0  # Oscillate between 0 and 1
        color = interpolate_color(base_color, glow_color, factor)
        yield Text(WELCOME_ASCII_ART, style=Style(color=color, bold=True))

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
        # Matrix effect
        for frame in animate_matrix(WELCOME_ASCII_ART):
            live.update(frame)

        # # Glow effect
        # for frame in animate_glow():
        #     panel = Panel(
        #         Group(
        #             frame,
        #             Text("\n")
        #             # welcome_text
        #         ),
        #         box=box.ROUNDED,
        #         border_style="bold cyan",
        #         title="Willy VanSickle's AI Assistant",
        #         title_align="center",
        #     )
        #     live.update(panel)
        #     time.sleep(0.05)

        # Rainbow effect
        for frame in animate_rainbow():
            panel = Panel(
                Group(
                    frame,
                    Text("\n")
                    
                ),
                box=box.ROUNDED,
                border_style="bold cyan",
                title="Willy VanSickle's AI Assistant",
                title_align="center",
            )
            live.update(panel)
            time.sleep(0.03)  # Reduced from 0.05 to speed up the rainbow effect

        # Typing effect for welcome message
        for typed_text in animate_typing(WELCOME_MESSAGE, speed=0.01):  # Reduced speed from 0.01 to 0.005
            panel = Panel(
                Group(
                    Text(WELCOME_ASCII_ART, style="bold cyan"),
                    Text("\n"),
                    typed_text
                ),
                box=box.ROUNDED,
                border_style="bold cyan",
                title="Willy VanSickle's AI Assistant",
                title_align="center",
            )
            live.update(panel)

    # Keep the final frame visible
    console.print(panel)