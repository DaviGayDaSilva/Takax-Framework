#!/usr/bin/env python3
"""
Terminal Display - Real-time terminal output rendering with ANSI colors
"""

import sys
import os
import time
from typing import Optional, List


class TerminalDisplay:
    """Handles terminal output with colors and formatting"""
    
    # ANSI Color codes
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m',
        
        # Foreground colors
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        
        # Background colors
        'bg_black': '\033[40m',
        'bg_red': '\033[41m',
        'bg_green': '\033[42m',
        'bg_yellow': '\033[43m',
        'bg_blue': '\033[44m',
        'bg_magenta': '\033[45m',
        'bg_cyan': '\033[46m',
        'bg_white': '\033[47m',
    }
    
    # Unicode symbols
    SYMBOLS = {
        'success': '✓',
        'error': '✗',
        'warning': '⚠',
        'info': 'ℹ',
        'progress': '▓',
        'package': '📦',
        'build': '🔧',
        'rocket': '🚀',
        'computer': '💻',
        'terminal': '⌨',
        'gear': '⚙',
        'sparkle': '✨',
    }
    
    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors and self._supports_color()
        self.buffer = []
        
    def _supports_color(self) -> bool:
        """Check if terminal supports colors"""
        if not hasattr(sys.stdout, 'isatty'):
            return False
        if not sys.stdout.isatty():
            return False
        # Check for common terminal environments
        return os.environ.get('TERM', '') not in ('', 'dumb')
        
    def _color(self, color: str) -> str:
        """Apply color if supported"""
        if self.use_colors:
            return self.COLORS.get(color, '')
        return ''
        
    def print(self, text: str = '', end: str = '\n'):
        """Print text with optional color"""
        print(text, end=end)
        
    def print_color(self, text: str, color: str, bold: bool = False):
        """Print text with specific color"""
        prefix = self._color('bold') if bold else ''
        color_code = self._color(color)
        suffix = self._color('reset')
        print(f"{prefix}{color_code}{text}{suffix}")
        
    def print_header(self, text: str):
        """Print header with decorative border"""
        width = 60
        line = '═' * width
        self.print_color(line, 'cyan', bold=True)
        self.print_color(text.center(width), 'cyan', bold=True)
        self.print_color(line, 'cyan', bold=True)
        
    def print_line(self):
        """Print a separator line"""
        self.print('─' * 60)
        
    def print_success(self, text: str):
        """Print success message"""
        symbol = self.SYMBOLS['success']
        self.print_color(f"  {symbol} {text}", 'green')
        
    def print_error(self, text: str):
        """Print error message"""
        symbol = self.SYMBOLS['error']
        self.print_color(f"  {symbol} {text}", 'red', bold=True)
        
    def print_warning(self, text: str):
        """Print warning message"""
        symbol = self.SYMBOLS['warning']
        self.print_color(f"  {symbol} {text}", 'yellow')
        
    def print_info(self, text: str):
        """Print info message"""
        symbol = self.SYMBOLS['info']
        self.print(f"  {symbol} {text}")
        
    def print_package(self, text: str):
        """Print package-related message"""
        symbol = self.SYMBOLS['package']
        self.print(f"  {symbol} {text}")
        
    def print_build(self, text: str):
        """Print build-related message"""
        symbol = self.SYMBOLS['build']
        self.print(f"  {symbol} {text}")
        
    def print_progress(self, current: int, total: int, prefix: str = ''):
        """Print progress bar"""
        if total == 0:
            return
            
        percent = current / total
        bar_length = 30
        filled = int(bar_length * percent)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        prefix_text = f"{prefix} " if prefix else ""
        self.print(f"\r  {prefix_text}[{bar}] {int(percent*100)}%", end='')
        
        if current >= total:
            self.print()
            
    def print_typing(self, text: str, delay: float = 0.03):
        """Print text with typing animation"""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()
        
    def clear(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def save_cursor(self):
        """Save cursor position"""
        sys.stdout.write('\033[s')
        
    def restore_cursor(self):
        """Restore cursor position"""
        sys.stdout.write('\033[u')
        
    def move_up(self, lines: int = 1):
        """Move cursor up"""
        sys.stdout.write(f'\033[{lines}A')
        
    def move_down(self, lines: int = 1):
        """Move cursor down"""
        sys.stdout.write(f'\033[{lines}B')
        
    def move_to_column(self, column: int):
        """Move cursor to specific column"""
        sys.stdout.write(f'\033[{column}G')
        
    # Stream handling for real-time terminal output
    def stream_output(self, generator):
        """Stream output from a generator in real-time"""
        for line in generator:
            print(line)
            self.buffer.append(line)
            
    def stream_with_status(self, steps: List[str], executor):
        """Execute steps and stream output with status updates"""
        total = len(steps)
        
        for i, step in enumerate(steps):
            self.print(f"\n📋 {step}")
            result = executor(step)
            
            if result:
                self.print_success(f"Completed: {step}")
            else:
                self.print_error(f"Failed: {step}")
                
            self.print_progress(i + 1, total)
            
    def get_buffer(self) -> List[str]:
        """Get accumulated output buffer"""
        return self.buffer
        
    def clear_buffer(self):
        """Clear output buffer"""
        self.buffer = []
        
    def export_log(self, filepath: str):
        """Export buffer to file"""
        with open(filepath, 'w') as f:
            f.write('\n'.join(self.buffer))
        self.print_info(f"Log exported to: {filepath}")


def demo():
    """Demonstrate terminal display features"""
    term = TerminalDisplay()
    
    term.print_header("Takax Terminal Demo")
    term.print()
    term.print_success("Success message")
    term.print_error("Error message")
    term.print_warning("Warning message")
    term.print_info("Info message")
    term.print_package("Installing package...")
    term.print_build("Building system...")
    term.print()
    term.print_line()
    
    # Progress bar demo
    for i in range(11):
        term.print_progress(i, 10, "Progress")
        time.sleep(0.1)
        
    term.print()
    term.print_success("Demo complete!")


if __name__ == '__main__':
    demo()