#!/usr/bin/env python3
"""
Takax CLI - Main entry point for command-line interface
Creates Linux operating systems via natural language chat
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.chat import ChatHandler
from cli.terminal import TerminalDisplay
from cli.config import ConfigManager
from cli.templates import TemplateManager


class TakaxCLI:
    """Main CLI application for Takax Framework"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = ConfigManager(config_path)
        self.terminal = TerminalDisplay()
        self.chat_handler = ChatHandler(self.config, self.terminal)
        self.templates = TemplateManager()
        
    def start_interactive(self):
        """Start interactive chat mode"""
        self.terminal.print_header("Takax Framework v1.0.0")
        self.terminal.print_info("Creating Linux OS via chat - Interactive Mode")
        self.terminal.print_line()
        
        # Show available templates
        templates = self.templates.list_templates()
        self.terminal.print_info("Available templates:")
        for name, desc in templates.items():
            self.terminal.print(f"  • {name}: {desc}")
        self.terminal.print_line()
        
        # Start chat loop
        print("\n🎯 Describe your OS (or 'quit' to exit):")
        print("   Example: 'Create a minimal Debian with Python and SSH'\n")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.terminal.print_info("Goodbye! 👋")
                    break
                    
                if not user_input:
                    continue
                    
                # Process the request
                self.chat_handler.process_message(user_input)
                
            except KeyboardInterrupt:
                self.terminal.print_info("\nInterrupted. Goodbye!")
                break
            except Exception as e:
                self.terminal.print_error(f"Error: {str(e)}")
                
    def build_from_template(self, template_name: str, output_dir: str):
        """Build OS from a template"""
        self.terminal.print_header(f"Building from template: {template_name}")
        
        template = self.templates.get_template(template_name)
        if not template:
            self.terminal.print_error(f"Template '{template_name}' not found")
            return False
            
        # Execute build
        from sandbox.builder import BuildEngine
        builder = BuildEngine(self.config, self.terminal)
        
        try:
            result = builder.build_from_recipe(template, output_dir)
            if result:
                self.terminal.print_success(f"\n✅ Build complete! Output: {output_dir}")
                return True
        except Exception as e:
            self.terminal.print_error(f"Build failed: {str(e)}")
            
        return False
    
    def build_from_description(self, description: str, output_dir: str):
        """Build OS from natural language description"""
        self.terminal.print_header("Building OS from description")
        self.terminal.print(f"Description: {description}\n")
        
        # Parse description and create recipe
        from sandbox.recipe import RecipeParser
        parser = RecipeParser()
        recipe = parser.parse_description(description)
        
        # Execute build
        from sandbox.builder import BuildEngine
        builder = BuildEngine(self.config, self.terminal)
        
        try:
            result = builder.build_from_recipe(recipe, output_dir)
            if result:
                self.terminal.print_success(f"\n✅ Build complete! Output: {output_dir}")
                return True
        except Exception as e:
            self.terminal.print_error(f"Build failed: {str(e)}")
            
        return False
    
    def list_projects(self):
        """List saved projects"""
        projects_dir = self.config.get('projects_dir', '.takax/projects')
        projects_path = Path(projects_dir)
        
        if not projects_path.exists():
            self.terminal.print_info("No projects found")
            return
            
        self.terminal.print_header("Saved Projects")
        for project in projects_path.iterdir():
            if project.is_dir():
                meta_file = project / 'metadata.json'
                if meta_file.exists():
                    with open(meta_file) as f:
                        meta = json.load(f)
                    self.terminal.print(f"  • {project.name} - {meta.get('description', 'No description')}")
                else:
                    self.terminal.print(f"  • {project.name}")
                    
    def load_project(self, project_name: str):
        """Load and continue a project"""
        projects_dir = self.config.get('projects_dir', '.takax/projects')
        project_path = Path(projects_dir) / project_name / 'metadata.json'
        
        if not project_path.exists():
            self.terminal.print_error(f"Project '{project_name}' not found")
            return
            
        with open(project_path) as f:
            meta = json.load(f)
            
        self.terminal.print_header(f"Project: {project_name}")
        self.terminal.print(f"Description: {meta.get('description', 'N/A')}")
        self.terminal.print(f"Created: {meta.get('created_at', 'N/A')}")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Takax - Create Linux OS via chat',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  takax                              # Start interactive mode
  takax -t debian-minimal            # Build from template
  takax -d "Minimal Ubuntu with Docker"  # Build from description
  takax --list-projects              # List saved projects
  takax --project my-os              # Load existing project
        """
    )
    
    parser.add_argument(
        '-t', '--template',
        help='Build from template name'
    )
    
    parser.add_argument(
        '-d', '--description',
        help='Build from natural language description'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='./takax-output',
        help='Output directory (default: ./takax-output)'
    )
    
    parser.add_argument(
        '--list-projects',
        action='store_true',
        help='List saved projects'
    )
    
    parser.add_argument(
        '-p', '--project',
        help='Load and continue existing project'
    )
    
    parser.add_argument(
        '-c', '--config',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = TakaxCLI(args.config)
    
    # Execute commands
    if args.list_projects:
        cli.list_projects()
    elif args.project:
        cli.load_project(args.project)
    elif args.template:
        cli.build_from_template(args.template, args.output)
    elif args.description:
        cli.build_from_description(args.description, args.output)
    else:
        cli.start_interactive()


if __name__ == '__main__':
    main()