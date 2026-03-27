#!/usr/bin/env python3
"""
Templates - Pre-defined OS build templates
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class OSTemplate:
    """OS Build Template"""
    name: str
    description: str
    base_image: str
    packages: List[str]
    config: Dict
    type: str = "minimal"


class TemplateManager:
    """Manages OS build templates"""
    
    def __init__(self):
        self.templates = self._load_default_templates()
        
    def _load_default_templates(self) -> Dict[str, OSTemplate]:
        """Load default templates"""
        return {
            'debian-minimal': OSTemplate(
                name='debian-minimal',
                description='Minimal Debian base system',
                base_image='debian:bookworm-slim',
                packages=['base-files', ' libc-bin'],
                config={'type': 'minimal', 'size': 'minimal'}
            ),
            
            'ubuntu-server': OSTemplate(
                name='ubuntu-server',
                description='Ubuntu Server with common tools',
                base_image='ubuntu:22.04',
                packages=[
                    'openssh-server',
                    'curl',
                    'wget',
                    'git',
                    'vim',
                    'net-tools'
                ],
                config={
                    'type': 'server',
                    'ssh': {'enabled': True},
                    'hostname': 'takax-ubuntu'
                }
            ),
            
            'debian-python': OSTemplate(
                name='debian-python',
                description='Debian with Python development environment',
                base_image='debian:bookworm-slim',
                packages=[
                    'python3',
                    'python3-pip',
                    'python3-venv',
                    'git',
                    'curl'
                ],
                config={
                    'type': 'development',
                    'python': {'version': '3.11'}
                }
            ),
            
            'alpine-minimal': OSTemplate(
                name='alpine-minimal',
                description='Ultra-minimal Alpine Linux',
                base_image='alpine:latest',
                packages=['bash', 'openssl', 'ca-certificates'],
                config={'type': 'minimal', 'size': 'tiny'}
            ),
            
            'arch-linux': OSTemplate(
                name='arch-linux',
                description='Arch Linux base system',
                base_image='archlinux:latest',
                packages=[
                    'base',
                    'linux',
                    'openssh'
                ],
                config={'type': 'minimal'}
            ),
            
            'fedora-server': OSTemplate(
                name='fedora-server',
                description='Fedora Server edition',
                base_image='fedora:39',
                packages=[
                    'openssh-server',
                    'vim',
                    'curl',
                    'wget'
                ],
                config={
                    'type': 'server',
                    'ssh': {'enabled': True}
                }
            ),
            
            'docker-host': OSTemplate(
                name='docker-host',
                description='Minimal system with Docker support',
                base_image='debian:bookworm-slim',
                packages=[
                    'docker.io',
                    'docker-compose',
                    'curl',
                    'openssh-server'
                ],
                config={
                    'type': 'container-host',
                    'docker': {'enabled': True, 'socket': True}
                }
            ),
            
            'dev-environment': OSTemplate(
                name='dev-environment',
                description='Full development environment',
                base_image='ubuntu:22.04',
                packages=[
                    'build-essential',
                    'python3',
                    'python3-pip',
                    'nodejs',
                    'npm',
                    'git',
                    'vim',
                    'curl',
                    'openssh-server',
                    'docker.io'
                ],
                config={
                    'type': 'development',
                    'tools': ['docker', 'node', 'python']
                }
            ),
            
            'web-server': OSTemplate(
                name='web-server',
                description='Web hosting server with Nginx',
                base_image='debian:bookworm-slim',
                packages=[
                    'nginx',
                    'python3',
                    'python3-pip',
                    'curl',
                    'openssh-server',
                    'certbot'
                ],
                config={
                    'type': 'server',
                    'webserver': {'nginx': True, 'php': False}
                }
            ),
            
            'security- hardened': OSTemplate(
                name='security-hardened',
                description='Security-hardened minimal system',
                base_image='debian:bookworm-slim',
                packages=[
                    'openssh-server',
                    'fail2ban',
                    'auditd',
                    'aide'
                ],
                config={
                    'type': 'security',
                    'firewall': True,
                    'hardening': True
                }
            ),
        }
        
    def list_templates(self) -> Dict[str, str]:
        """List all available templates"""
        return {name: tmpl.description for name, tmpl in self.templates.items()}
        
    def get_template(self, name: str) -> OSTemplate:
        """Get template by name"""
        return self.templates.get(name)
        
    def add_template(self, template: OSTemplate):
        """Add custom template"""
        self.templates[template.name] = template
        
    def remove_template(self, name: str) -> bool:
        """Remove custom template"""
        if name in self.templates:
            del self.templates[name]
            return True
        return False
        
    def export_template(self, name: str) -> Dict:
        """Export template as dictionary"""
        template = self.get_template(name)
        if not template:
            return {}
            
        return {
            'name': template.name,
            'description': template.description,
            'base_image': template.base_image,
            'packages': template.packages,
            'config': template.config,
            'type': template.type
        }


# Template examples for the user
TEMPLATE_EXAMPLES = """
Example template definitions:

# Minimal Debian
name: debian-minimal
base: debian:bookworm-slim
packages:
  - base-files
  - libc-bin
type: minimal

# Python Development
name: python-dev
base: ubuntu:22.04
packages:
  - python3
  - python3-pip
  - build-essential
type: development

# Web Server
name: web-server  
base: debian:bookworm-slim
packages:
  - nginx
  - php-fpm
  - mariadb-server
type: server
"""