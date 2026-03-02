"""
变量池服务

管理批量执行多个测试用例时的变量传递。

支持四种变量作用域：
1. env   - 环境变量（只读，来自测试环境配置）
2. global - 全局变量（跨用例共享，整个执行周期有效）
3. shared - 共享变量（用例间传递，由提取引擎填充）
4. local  - 局部变量（仅当前用例有效，每个用例执行前清空）

变量引用格式: ${scope.variable_name}
示例: ${env.base_url}, ${global.token}, ${shared.user_id}
"""

import logging
import re
from typing import Any, Dict, Optional

from api_automation.models import ApiTestEnvironment

logger = logging.getLogger(__name__)


class VariablePool:
    """
    变量池

    管理批量执行时的变量存储和传递。每个作用域独立管理，
    支持嵌套属性访问和 ${scope.name} 格式的占位符替换。
    """

    # 变量引用的正则模式：匹配 ${scope.variable_name} 格式
    VARIABLE_PATTERN = re.compile(r'\$\{([a-z_]+\.[-a-zA-Z0-9_.]+)\}')

    def __init__(self, environment: Optional[ApiTestEnvironment] = None):
        """
        初始化变量池

        Args:
            environment: 测试环境对象，用于初始化env作用域的变量
        """
        self.pool = {
            'env': {},      # 环境变量（只读）
            'global': {},   # 全局变量（跨用例共享）
            'shared': {},   # 共享变量（用例间传递）
            'local': {},    # 局部变量（仅当前用例）
        }

        if environment:
            self._init_env_variables(environment)

    def _init_env_variables(self, environment: ApiTestEnvironment):
        """
        从测试环境对象初始化环境变量

        将环境的 base_url 和所有全局变量加载到 env 作用域。

        Args:
            environment: 测试环境对象
        """
        self.pool['env'] = {
            'base_url': environment.base_url,
            **environment.global_variables,
        }

    def get(self, variable_path: str, default: Any = None) -> Any:
        """
        按路径获取变量值

        支持多级嵌套访问，如 'shared.user.id' 会依次查找
        pool['shared']['user']['id']。

        Args:
            variable_path: 变量路径（格式: scope.name 或 scope.nested.name）
            default: 变量不存在时的默认返回值

        Returns:
            变量值，不存在时返回default
        """
        try:
            parts = variable_path.split('.')
            if len(parts) < 2:
                logger.warning(f"Invalid variable path: {variable_path}")
                return default

            scope = parts[0]
            var_name = '.'.join(parts[1:])

            if scope not in self.pool:
                logger.warning(f"Unknown variable scope: {scope}")
                return default

            # 逐级嵌套访问
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
        按路径设置变量值

        自动创建中间层级的字典。env作用域为只读，不允许修改。

        Args:
            variable_path: 变量路径
            value: 要设置的值
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

            # 环境变量为只读
            if scope == 'env':
                logger.warning("Cannot modify environment variables")
                return

            # 逐级创建嵌套字典并设置值
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
        """添加共享变量（用例间传递）"""
        self.pool['shared'][name] = value
        logger.debug(f"Added shared variable: {name} = {value}")

    def get_shared_variable(self, name: str, default: Any = None) -> Any:
        """获取共享变量"""
        return self.pool['shared'].get(name, default)

    def add_global_variable(self, name: str, value: Any):
        """添加全局变量（跨用例共享）"""
        self.pool['global'][name] = value
        logger.debug(f"Added global variable: {name} = {value}")

    def get_global_variable(self, name: str, default: Any = None) -> Any:
        """获取全局变量"""
        return self.pool['global'].get(name, default)

    def set_local_variables(self, variables: Dict[str, Any]):
        """批量设置局部变量（仅当前用例有效）"""
        self.pool['local'].update(variables)

    def get_local_variable(self, name: str, default: Any = None) -> Any:
        """获取局部变量"""
        return self.pool['local'].get(name, default)

    def clear_local_variables(self):
        """清空局部变量（每个用例执行前调用）"""
        self.pool['local'].clear()

    def to_dict(self) -> Dict[str, Any]:
        """
        将变量池导出为字典（各作用域独立拷贝，不影响原始数据）

        Returns:
            包含四个作用域的变量字典
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
        从字典反序列化创建变量池实例

        Args:
            data: 包含四个作用域的变量字典

        Returns:
            还原后的VariablePool实例
        """
        pool = cls()
        pool.pool = data
        return pool

    def replace_variables(self, text: str) -> str:
        """
        替换文本中的 ${scope.name} 格式变量占位符

        遍历文本中所有匹配 ${scope.variable_name} 模式的占位符，
        从变量池中查找对应值并替换。

        Args:
            text: 包含变量占位符的文本

        Returns:
            替换后的文本
        """
        if not text or not isinstance(text, str):
            return text

        def replacer(match):
            var_path = match.group(1)
            value = self.get(var_path, '')
            return str(value) if value is not None else ''

        try:
            return self.VARIABLE_PATTERN.sub(replacer, text)
        except Exception as e:
            logger.error(f"Error replacing variables: {e}")
            return text

    def replace_variables_in_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归替换字典中所有字符串值的变量占位符

        支持嵌套字典和列表中的字符串元素。

        Args:
            data: 包含变量占位符的字典

        Returns:
            替换后的新字典
        """
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.replace_variables(value)
            elif isinstance(value, dict):
                result[key] = self.replace_variables_in_dict(value)
            elif isinstance(value, list):
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
        """获取所有共享变量的拷贝"""
        return self.pool['shared'].copy()

    def get_all_global_variables(self) -> Dict[str, Any]:
        """获取所有全局变量的拷贝"""
        return self.pool['global'].copy()

    def __repr__(self) -> str:
        """返回变量池的简要状态信息"""
        return (
            f"<VariablePool env={len(self.pool['env'])} "
            f"global={len(self.pool['global'])} "
            f"shared={len(self.pool['shared'])}>"
        )
