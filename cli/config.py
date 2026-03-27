#!/usr/bin/env python3
"""
Config Manager - Handles CLI configuration and settings
"""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages configuration for Takax CLI"""
    
    DEFAULT_CONFIG = {
        'output_dir': './takax-output',
        'projects_dir': '.takax/projects',
        'cache_dir': '.takax/cache',
        'sandbox': {
            'type': 'docker',
            'image': 'debian:stable',
            'memory_limit': '2g',
            'cpu_limit': 2,
            'disk_limit': '10g',
        },
        'build': {
            'parallel': True,
            'clean_after': True,
            'compress_output': True,
        },
        'llm': {
            'provider': 'openai',
            'model': 'gpt-4',
            'api_key': None,
        },
        'terminal': {
            'colors': True,
            'unicode': True,
            'animations': True,
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_path = config_path or self._get_default_config_path()
        self.load()
        
    def _get_default_config_path(self) -> str:
        """Get default config file path"""
        home = Path.home()
        return str(home / '.takax' / 'config.yaml')
        
    def load(self):
        """Load configuration from file"""
        if not self.config_path:
            return
            
        config_file = Path(self.config_path)
        
        if config_file.exists():
            with open(config_file) as f:
                if config_file.suffix in ['.yaml', '.yml']:
                    loaded = yaml.safe_load(f)
                elif config_file.suffix == '.json':
                    loaded = json.load(f)
                else:
                    return
                    
                if loaded:
                    self._merge_config(loaded)
                    
    def _merge_config(self, loaded: Dict):
        """Merge loaded config with defaults"""
        for key, value in loaded.items():
            if key in self.config and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
                
    def save(self, path: Optional[str] = None):
        """Save configuration to file"""
        save_path = path or self.config_path
        
        if not save_path:
            return
            
        config_file = Path(save_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    def set(self, key: str, value: Any):
        """Set configuration value by key"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        
    def get_sandbox_config(self) -> Dict:
        """Get sandbox configuration"""
        return self.config.get('sandbox', {})
        
    def get_build_config(self) -> Dict:
        """Get build configuration"""
        return self.config.get('build', {})
        
    def get_llm_config(self) -> Dict:
        """Get LLM configuration"""
        return self.config.get('llm', {})
        
    def update_llm_provider(self, provider: str, api_key: str = None):
        """Update LLM provider settings"""
        self.config['llm']['provider'] = provider
        if api_key:
            self.config['llm']['api_key'] = api_key
            
    def validate(self) -> tuple[bool, list]:
        """Validate configuration"""
        errors = []
        
        # Validate sandbox settings
        sandbox = self.config.get('sandbox', {})
        if not sandbox.get('image'):
            errors.append("Sandbox image is required")
            
        # Validate LLM settings
        llm = self.config.get('llm', {})
        if not llm.get('provider'):
            errors.append("LLM provider is required")
            
        return len(errors) == 0, errors
        
    def reset(self):
        """Reset to default configuration"""
        self.config = self.DEFAULT_CONFIG.copy()


# CLI-specific helpers
def get_config_from_env() -> Dict:
    """Get configuration from environment variables"""
    config = {}
    
    # LLM config from env
    if api_key := os.environ.get('TAKAX_OPENAI_API_KEY'):
        config['llm'] = {'provider': 'openai', 'api_key': api_key}
    elif api_key := os.environ.get('TAKAX_ANTHROPIC_API_KEY'):
        config['llm'] = {'provider': 'anthropic', 'api_key': api_key}
        
    # Sandbox config from env
    if image := os.environ.get('TAKAX_SANDBOX_IMAGE'):
        config['sandbox'] = {'image': image}
        
    return config


def create_default_config(path: str):
    """Create default configuration file"""
    config_file = Path(path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        yaml.dump(ConfigManager.DEFAULT_CONFIG, f, default_flow_style=False)
        
    return config_file