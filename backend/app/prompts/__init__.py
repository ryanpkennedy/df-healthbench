"""
Prompt management utilities for loading prompts from YAML files.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

_prompts_cache: Dict[str, Any] = {}


def load_prompts(filename: str) -> Dict[str, Any]:
    """
    Load prompts from a YAML file in the prompts directory.
    
    Args:
        filename: Name of the YAML file (e.g., 'agent_extraction.yaml')
    
    Returns:
        Dictionary containing the prompts from the file
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
    """
    # Cache prompts to avoid reloading
    if filename in _prompts_cache:
        return _prompts_cache[filename]
    
    prompts_dir = Path(__file__).parent
    file_path = prompts_dir / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        prompts = yaml.safe_load(f)
    
    _prompts_cache[filename] = prompts
    return prompts


def get_prompt(filename: str, key: str) -> str:
    """
    Get a specific prompt by key from a YAML file.
    
    Args:
        filename: Name of the YAML file
        key: Key of the prompt to retrieve
    
    Returns:
        The prompt string
        
    Raises:
        KeyError: If the key doesn't exist in the prompts file
    """
    prompts = load_prompts(filename)
    
    if key not in prompts:
        raise KeyError(f"Prompt key '{key}' not found in {filename}")
    
    return prompts[key]

