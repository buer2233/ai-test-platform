"""
variable_pool_service.py

变量池服务，用于在批量执行多个测试用例时管理变量传递。

支持三种变量作用域：
1. env - 环境变量（只读）
2. global - 全局变量（跨用例共享）
3. shared - 共享变量（用例间传递）
"""
import re
import logging
from typing import Dict, Any, Optional
from api_automation.models import ApiTestEnvironment, ApiTestCase

logger = logging.getLogger(__name__)


class VariablePool:
    """
    变量池，用于管理批量执行时的变量传递
    """

    def __init__(self, environment: Optional[ApiTestEnvironment] = None):
        """
        初始化变量池

        Args:
            environment: 测试环境对象
        """
        self.pool = {
            'env': {},      # 环境变量（只读）
            'global': {},   # 全局变量（跨用例共享）
            'shared': {},   # 共享变量（用例间传递）
            'local': {},    # 局部变量（仅当前用例）
        }

        # 初始化环境变量
        if environment:
            self._init_env_variables(environment)

    def _init_env_variables(self, environment: ApiTestEnvironment):
        """初始化环境变量"""
        self.pool['env'] = {
            'base_url': environment.base_url,
            **environment.global_variables,
        }

    def get(self, variable_path: str, default: Any = None) -> Any:
        """
        获取变量值

        Args:
            variable_path: 变量路径，如 'env.base_url', 'global.token', 'shared.user_id'
            default: 默认值

        Returns:
            变量值
        """
        try:
            # 解析变量路径
            parts = variable_path.split('.')
            if len(parts) < 2:
                logger.warning(f"Invalid variable path: {variable_path}")
                return default

            scope = parts[0]
            var_name = '.'.join(parts[1:])

            if scope not in self.pool:
                logger.warning(f"Unknown variable scope: {scope}")
                return default

            # 支持嵌套访问，如 shared.user.id
            value = self.pool[scope]
            for key in var_name.split('.'):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return default

            return value if value is not None else default

        except Exception as e:
            logger.error(f"Error getting variable {variable_path}: {e}")
            return default

    def set(self, variable_path: str, value: Any):
        """
        设置变量值

        Args:
            variable_path: 变量路径
            value: 变量值
        """
        try:
            parts = variable_path.split('.')
            if len(parts) < 2:
                logger.warning(f"Invalid variable path: {variable_path}")
                return

            scope = parts[0]
            var_name = '.'.join(parts[1:])

            if scope not in self.pool:
                logger.warning(f"Unknown variable scope: {scope}")
                return

            # 环境变量不允许修改
            if scope == 'env':
                logger.warning(f"Cannot modify environment variables")
                return

            # 支持嵌套设置
            current = self.pool[scope]
            keys = var_name.split('.')

            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            current[keys[-1]] = value
            logger.debug(f"Set variable: {variable_path} = {value}")

        except Exception as e:
            logger.error(f"Error setting variable {variable_path}: {e}")

    def add_shared_variable(self, name: str, value: Any):
        """
        添加共享变量（用例间传递）

        Args:
            name: 变量名
            value: 变量值
        """
        self.pool['shared'][name] = value
        logger.debug(f"Added shared variable: {name} = {value}")

    def get_shared_variable(self, name: str, default: Any = None) -> Any:
        """
        获取共享变量

        Args:
            name: 变量名
            default: 默认值

        Returns:
            变量值
        """
        return self.pool['shared'].get(name, default)

    def add_global_variable(self, name: str, value: Any):
        """
        添加全局变量

        Args:
            name: 变量名
            value: 变量值
        """
        self.pool['global'][name] = value
        logger.debug(f"Added global variable: {name} = {value}")

    def get_global_variable(self, name: str, default: Any = None) -> Any:
        """
        获取全局变量

        Args:
            name: 变量名
            default: 默认值

        Returns:
            变量值
        """
        return self.pool['global'].get(name, default)

    def set_local_variables(self, variables: Dict[str, Any]):
        """
        设置局部变量（当前用例）

        Args:
            variables: 变量字典
        """
        self.pool['local'].update(variables)

    def get_local_variable(self, name: str, default: Any = None) -> Any:
        """
        获取局部变量

        Args:
            name: 变量名
            default: 默认值

        Returns:
            变量值
        """
        return self.pool['local'].get(name, default)

    def clear_local_variables(self):
        """清除局部变量"""
        self.pool['local'].clear()

    def to_dict(self) -> Dict[str, Any]:
        """
        导出变量池为字典

        Returns:
            变量池字典
        """
        return {
            'env': self.pool['env'].copy(),
            'global': self.pool['global'].copy(),
            'shared': self.pool['shared'].copy(),
            'local': self.pool['local'].copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VariablePool':
        """
        从字典创建变量池

        Args:
            data: 变量池字典

        Returns:
            VariablePool实例
        """
        pool = cls()
        pool.pool = data
        return pool

    def replace_variables(self, text: str) -> str:
        """
        替换文本中的变量占位符

        支持的格式：
        - ${env.base_url}
        - ${global.token}
        - ${shared.user_id}
        - ${local.username}

        Args:
            text: 包含变量占位符的文本

        Returns:
            替换后的文本
        """
        if not text or not isinstance(text, str):
            return text

        # 匹配 ${scope.name} 格式的变量
        pattern = r'\$\{([a-z_]+\.[-a-zA-Z0-9_.]+)\}'

        def replacer(match):
            var_path = match.group(1)
            value = self.get(var_path, '')
            return str(value) if value is not None else ''

        try:
            result = re.sub(pattern, replacer, text)
            return result
        except Exception as e:
            logger.error(f"Error replacing variables: {e}")
            return text

    def replace_variables_in_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归替换字典中的变量

        Args:
            data: 包含变量的字典

        Returns:
            替换后的字典
        """
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                # 替换字符串中的变量
                result[key] = self.replace_variables(value)
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                result[key] = self.replace_variables_in_dict(value)
            elif isinstance(value, list):
                # 处理列表
                result[key] = [
                    self.replace_variables_in_dict(item) if isinstance(item, dict)
                    else self.replace_variables(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def get_all_shared_variables(self) -> Dict[str, Any]:
        """
        获取所有共享变量

        Returns:
            共享变量字典
        """
        return self.pool['shared'].copy()

    def get_all_global_variables(self) -> Dict[str, Any]:
        """
        获取所有全局变量

        Returns:
            全局变量字典
        """
        return self.pool['global'].copy()

    def __repr__(self) -> str:
        return f"<VariablePool env={len(self.pool['env'])} global={len(self.pool['global'])} shared={len(self.pool['shared'])}>"
