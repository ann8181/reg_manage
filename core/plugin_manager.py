"""
插件管理器
支持任务插件的自动发现
"""
from pathlib import Path
from typing import Dict, List, Any
import logging
import importlib.util

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self._plugins: Dict[str, Any] = {}
    
    def discover_tasks(self) -> Dict[str, Any]:
        discovered = {}
        
        if not self.plugin_dir.exists():
            logger.warning(f"Plugin directory {self.plugin_dir} does not exist")
            return discovered
        
        for task_dir in self.plugin_dir.rglob("task.yaml"):
            try:
                import yaml
                with open(task_dir, 'r') as f:
                    config = yaml.safe_load(f)
                
                module_path = task_dir.parent
                discovered[config.get("name", module_path.name)] = {
                    "path": str(module_path),
                    "config": config
                }
                logger.info(f"Discovered plugin: {module_path.name}")
            except Exception as e:
                logger.error(f"Failed to load plugin {task_dir}: {e}")
        
        return discovered
    
    def load_plugin(self, name: str) -> Any:
        if name in self._plugins:
            return self._plugins[name]
        
        discovered = self.discover_tasks()
        if name not in discovered:
            raise ValueError(f"Plugin {name} not found")
        
        plugin_info = discovered[name]
        spec = importlib.util.spec_from_file_location(
            name, 
            Path(plugin_info["path"]) / "__init__.py"
        )
        
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._plugins[name] = module
        
        return self._plugins[name]
    
    def list_plugins(self) -> List[str]:
        return list(self.discover_tasks().keys())