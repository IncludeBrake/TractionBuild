"""
YAML loader utilities for ZeroToShip.
"""

import yaml
from typing import Dict, Any, Optional
from pathlib import Path


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Configuration dictionary
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml_config(data: Dict[str, Any], file_path: str) -> None:
    """
    Save data to YAML configuration file.
    
    Args:
        data: Data to save
        file_path: Path to YAML file
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, indent=2)


def merge_yaml_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple YAML configurations.
    
    Args:
        *configs: Configuration dictionaries to merge
        
    Returns:
        Merged configuration
    """
    if not configs:
        return {}
    
    result = configs[0].copy()
    
    for config in configs[1:]:
        _deep_merge(result, config)
    
    return result


def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> None:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        update: Update dictionary
    """
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value 