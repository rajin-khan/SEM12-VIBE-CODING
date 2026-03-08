"""
NSU Graduation Auditor - Simple Header (no mascot)
"""

from rich.console import Console

console = Console()

# Bright Colors
BRIGHT_BLUE = "#00BFFF"  # Deep Sky Blue - very bright
VERMILLION = "#FF4500"   # Orange Red - bright vermillion


class Mascot:
    """Simple header for NSU Graduation Auditor"""
    
    def __init__(self, style='simple'):
        self.displayed = False
    
    def show(self):
        """Show simple header"""
        if not self.displayed:
            console.print()
            console.print(f"[bold {BRIGHT_BLUE}]╔═══════════════════════════════════════════════════╗[/]")
            console.print(f"[bold {BRIGHT_BLUE}]║  [/][bold {VERMILLION}]NSU GRADUATION AUDITOR[/][bold {BRIGHT_BLUE}]                           ║[/]")
            console.print(f"[bold {BRIGHT_BLUE}]║  [/][dim]Checking your path to graduation...[/][bold {BRIGHT_BLUE}]              ║[/]")
            console.print(f"[bold {BRIGHT_BLUE}]╚═══════════════════════════════════════════════════╝[/]")
            console.print()
            self.displayed = True
    
    def show_thinking(self):
        """Show loading message"""
        console.print(f"[dim {VERMILLION}]◈[/] [dim]Loading transcript data...[/]")
    
    def show_complete(self):
        """Show completion message"""
        console.print()
        console.print(f"[bold {VERMILLION}]✦ Audit Complete ✦[/]")
        console.print()


# Default mascot instance
mascot = Mascot()
