#!/usr/bin/env python3
"""
Chat Handler - Processes natural language requests using Devstral AI
"""

import re
import json
import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime


# Devstral AI Configuration
DEVSTRAL_CONFIG = {
    "model": "devstral",
    "api_url": os.environ.get("DEVSTRAL_API_URL", "https://api.endpoints.ai/v1/chat/completions"),
    "api_key": os.environ.get("DEVSTRAL_API_KEY", ""),
    "temperature": 0.7,
    "max_tokens": 1024,
}


SYSTEM_PROMPT = """You are Takax, an AI assistant that helps create Linux operating systems from natural language.

Your job is to:
1. Analyze user requests for OS creation
2. Extract the distribution (Debian, Ubuntu, Arch, Fedora, Alpine)
3. Identify required packages and components
4. Determine the OS type (minimal, server, desktop, development)
5. Generate a build plan

Respond with a JSON object containing:
- detected_distro: the Linux distribution
- components: list of packages to install
- requirements: list of OS requirements (minimal, server, desktop)
- action: "build" if they want to create an OS, "analyze" otherwise
- confidence: how confident you are (0.0 to 1.0)
- message: a user-friendly response

Example:
Input: "Create a minimal Debian with Python and SSH"
Output: {"detected_distro": "debian", "components": ["python3", "openssh-server"], "requirements": ["minimal"], "action": "build", "confidence": 0.9}"""


class ChatHandler:
    """Handles chat interactions using Devstral AI"""
    
    def __init__(self, config, terminal_display):
        self.config = config
        self.terminal = terminal_display
        self.conversation_history = []
        self.current_project = None
        self.use_ai = True  # Default to using AI
        self._init_devstral()
        
    def _init_devstral(self):
        """Initialize Devstral connection"""
        self.api_url = os.environ.get("DEVSTRAL_API_URL", "https://api.endpoints.ai/v1/chat/completions")
        self.api_key = os.environ.get("DEVSTRAL_API_KEY", "")
        self.model = os.environ.get("DEVSTRAL_MODEL", "devstral")
        
    def process_message(self, message: str) -> Dict[str, Any]:
        """Process user message and generate response using Devstral"""
        self.conversation_history.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Use Devstral AI for analysis
        analysis = self._analyze_with_devstral(message)
        
        # Generate response
        response = self.generate_response(analysis)
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': response['message'],
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis
        })
        
        # If build is requested, execute it
        if analysis.get('action') == 'build':
            self.execute_build(analysis)
            
        return response
        
    def _analyze_with_devstral(self, message: str) -> Dict[str, Any]:
        """Use Devstral AI to analyze the request"""
        
        # If API not available, fall back to keyword-based analysis
        if not self.api_key:
            return self._keyword_analysis(message)
        
        try:
            # Call Devstral API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse JSON response
                try:
                    analysis = json.loads(content)
                    return analysis
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract JSON
                    return self._extract_json_from_text(content)
            else:
                # Fall back to keyword analysis
                return self._keyword_analysis(message)
                
        except Exception as e:
            print(f"Devstral API error: {e}")
            return self._keyword_analysis(message)
            
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response"""
        try:
            # Try to find JSON in the text
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return self._keyword_analysis("")
        
    def _keyword_analysis(self, message: str) -> Dict[str, Any]:
        """Fallback keyword-based analysis"""
        message_lower = message.lower()
        
        analysis = {
            'original': message,
            'detected_distro': None,
            'components': [],
            'requirements': [],
            'action': 'analyze',
            'confidence': 0.5,
            'ai_powered': False
        }
        
        # Detect distribution
        for distro in ['debian', 'ubuntu', 'arch', 'fedora', 'alpine']:
            if distro in message_lower:
                analysis['detected_distro'] = distro
                analysis['confidence'] += 0.3
                break
                
        # Detect components
        package_keywords = {
            'python': 'python3', 'python3': 'python3',
            'nodejs': 'nodejs', 'node': 'nodejs',
            'docker': 'docker.io',
            'ssh': 'openssh-server', 'openssh': 'openssh-server',
            'nginx': 'nginx',
            'apache': 'apache2',
            'mysql': 'mariadb-server', 'maria': 'mariadb-server',
            'postgres': 'postgresql',
            'redis': 'redis-server',
            'golang': 'golang', 'go': 'golang',
            'rust': 'rustc',
            'git': 'git',
            'curl': 'curl',
            'vim': 'vim',
            'php': 'php',
            'java': 'default-jdk',
        }
        
        for keyword, package in package_keywords.items():
            if keyword in message_lower and package not in analysis['components']:
                analysis['components'].append(package)
                
        # Detect requirements
        if 'minimal' in message_lower or 'basic' in message_lower:
            analysis['requirements'].append('minimal')
        if 'server' in message_lower:
            analysis['requirements'].append('server')
        if 'desktop' in message_lower or 'gui' in message_lower:
            analysis['requirements'].append('desktop')
            
        # Detect build action
        build_keywords = ['create', 'build', 'make', 'generate', 'setup']
        if any(kw in message_lower for kw in build_keywords):
            analysis['action'] = 'build'
            analysis['confidence'] = min(1.0, analysis['confidence'] + 0.3)
            
        # Default to debian if no distro specified
        if not analysis['detected_distro']:
            analysis['detected_distro'] = 'debian'
            
        return analysis
        
    def generate_response(self, analysis: Dict) -> Dict[str, Any]:
        """Generate response based on analysis"""
        
        if analysis.get('ai_powered'):
            message = f"🤖 **AI-Powered Analysis** (Devstral)\n\n"
        else:
            message = f"🤖 **Analysis**\n\n"
            
        if analysis['action'] == 'build':
            # Generate build plan
            distro = analysis['detected_distro']
            components = analysis['components']
            requirements = analysis['requirements']
            
            message += f"**Distribution:** {distro.title()}\n"
            
            if requirements:
                message += f"**Type:** {', '.join(r.title() for r in requirements)}\n"
                
            if components:
                message += f"**Components:** {', '.join(c for c in components)}\n"
                
            message += f"\n🔧 Starting build process...\n"
            
        else:
            message += f"I understand you want to create a Linux OS.\n\n"
            message += f"Please provide more details:\n"
            message += f"  • Which distribution? (Debian, Ubuntu, Arch, Fedora, Alpine)\n"
            message += f"  • What packages do you need? (Python, Docker, SSH, etc.)\n"
            message += f"  • Server or Desktop version?\n\n"
            message += f"Or just say 'create' followed by your requirements!"
            
        return {
            'message': message,
            'analysis': analysis
        }
        
    def execute_build(self, analysis: Dict):
        """Execute the OS build"""
        self.terminal.print_info("🔧 Starting build process...")
        
        from sandbox.builder import BuildEngine
        from sandbox.recipe import BuildRecipe
        
        recipe = BuildRecipe(
            name="Custom OS",
            base_image=self._get_base_image(analysis['detected_distro']),
            type=analysis['requirements'][0] if analysis['requirements'] else 'minimal',
            packages=analysis['components']
        )
        
        builder = BuildEngine(self.config, self.terminal)
        
        try:
            output_dir = self.config.get('output_dir', './takax-output')
            result = builder.build_from_recipe(recipe, output_dir)
            
            if result:
                self.terminal.print_success("\n✅ Build completed successfully!")
                self.terminal.print(f"📁 Output: {output_dir}")
            else:
                self.terminal.print_error("\n❌ Build failed")
                
        except Exception as e:
            self.terminal.print_error(f"Build error: {str(e)}")
            
    def _get_base_image(self, distro: str) -> str:
        """Get base image for distribution"""
        images = {
            'debian': 'debian:bookworm-slim',
            'ubuntu': 'ubuntu:22.04',
            'arch': 'archlinux:latest',
            'fedora': 'fedora:39',
            'alpine': 'alpine:latest'
        }
        return images.get(distro, 'debian:bookworm-slim')
        
    def save_project(self, name: str, metadata: Dict):
        """Save current project"""
        projects_dir = self.config.get('projects_dir', '.takax/projects')
        project_path = Path(projects_dir) / name
        
        project_path.mkdir(parents=True, exist_ok=True)
        
        metadata['saved_at'] = datetime.now().isoformat()
        metadata['conversation'] = self.conversation_history
        
        with open(project_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
            
        self.terminal.print_success(f"Project saved: {name}")
        
    def load_conversation(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history
        
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.terminal.print_info("Conversation cleared")


from pathlib import Path