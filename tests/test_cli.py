#!/usr/bin/env python3
"""
CLI Tests - Test CLI functionality
"""

import sys
import unittest
from pathlib import Path
from io import StringIO

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCLIImports(unittest.TestCase):
    """Test CLI module imports"""
    
    def test_import_chat(self):
        """Test chat module import"""
        from cli import chat
        self.assertIsNotNone(chat)
        
    def test_import_terminal(self):
        """Test terminal module import"""
        from cli import terminal
        self.assertIsNotNone(terminal)
        
    def test_import_config(self):
        """Test config module import"""
        from cli import config
        self.assertIsNotNone(config)
        
    def test_import_templates(self):
        """Test templates module import"""
        from cli import templates
        self.assertIsNotNone(templates)


class TestTerminalDisplay(unittest.TestCase):
    """Test terminal display functionality"""
    
    def test_terminal_creation(self):
        """Test terminal can be created"""
        from cli.terminal import TerminalDisplay
        term = TerminalDisplay()
        self.assertIsNotNone(term)
        
    def test_color_codes(self):
        """Test color codes exist"""
        from cli.terminal import TerminalDisplay
        term = TerminalDisplay(use_colors=False)
        self.assertIn('green', term.COLORS)
        self.assertIn('red', term.COLORS)
        self.assertIn('cyan', term.COLORS)
        
    def test_symbols(self):
        """Test symbols exist"""
        from cli.terminal import TerminalDisplay
        term = TerminalDisplay()
        self.assertIn('success', term.SYMBOLS)
        self.assertIn('error', term.SYMBOLS)


class TestConfigManager(unittest.TestCase):
    """Test configuration management"""
    
    def test_default_config(self):
        """Test default configuration"""
        from cli.config import ConfigManager
        config = ConfigManager()
        self.assertIsNotNone(config.config)
        
    def test_get_config(self):
        """Test getting config values"""
        from cli.config import ConfigManager
        config = ConfigManager()
        output_dir = config.get('output_dir')
        self.assertEqual(output_dir, './takax-output')
        
    def test_set_config(self):
        """Test setting config values"""
        from cli.config import ConfigManager
        config = ConfigManager()
        config.set('test_key', 'test_value')
        self.assertEqual(config.get('test_key'), 'test_value')


class TestTemplates(unittest.TestCase):
    """Test template system"""
    
    def test_template_list(self):
        """Test listing templates"""
        from cli.templates import TemplateManager
        tm = TemplateManager()
        templates = tm.list_templates()
        self.assertGreater(len(templates), 0)
        
    def test_get_template(self):
        """Test getting specific template"""
        from cli.templates import TemplateManager
        tm = TemplateManager()
        template = tm.get_template('debian-minimal')
        self.assertIsNotNone(template)
        self.assertEqual(template.name, 'debian-minimal')


class TestChatHandler(unittest.TestCase):
    """Test chat handler"""
    
    def test_chat_handler_creation(self):
        """Test chat handler can be created"""
        from cli.chat import ChatHandler
        from cli.config import ConfigManager
        from cli.terminal import TerminalDisplay
        
        config = ConfigManager()
        terminal = TerminalDisplay(use_colors=False)
        handler = ChatHandler(config, terminal)
        self.assertIsNotNone(handler)
        
    def test_analyze_request(self):
        """Test request analysis"""
        from cli.chat import ChatHandler
        from cli.config import ConfigManager
        from cli.terminal import TerminalDisplay
        
        config = ConfigManager()
        terminal = TerminalDisplay(use_colors=False)
        handler = ChatHandler(config, terminal)
        
        # Use the keyword analysis method (fallback when no API key)
        analysis = handler._keyword_analysis("Create a Debian with Python")
        
        self.assertEqual(analysis['detected_distro'], 'debian')
        # Python is mapped to python3 in the keyword analysis
        self.assertIn('python3', analysis['components'])
        self.assertEqual(analysis['action'], 'build')


if __name__ == '__main__':
    unittest.main()