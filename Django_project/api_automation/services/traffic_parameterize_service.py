"""
流量参数化服务

基于响应中的动态字段自动生成变量规则，并对后续请求进行替换。
"""

import copy


class ParameterizeService:
    """自动参数化与变量规则生成。"""

    DYNAMIC_KEYWORDS = ("token", "id", "session", "auth")

    def parameterize(self, entries):
        entries = copy.deepcopy(entries)
        variable_rules = []
        conflicts = []
        existing_names = set()
        value_map = {}

        for entry in entries:
            response_body = entry.get("response_body") or {}
            if isinstance(response_body, dict):
                for key, value in response_body.items():
                    if not self._is_dynamic_key(key):
                        continue
                    variable_name = key
                    if variable_name in existing_names:
                        conflicts.append(variable_name)
                        suffix = 1
                        while f"{variable_name}_{suffix}" in existing_names:
                            suffix += 1
                        variable_name = f"{variable_name}_{suffix}"

                    existing_names.add(variable_name)
                    value_map[key] = (value, variable_name)
                    variable_rules.append({
                        "variable_name": variable_name,
                        "source_type": "JSONPATH",
                        "expression": f"$.{key}",
                        "target_scope": "SCENARIO",
                    })

        for entry in entries:
            entry["request_params"] = self._replace_values(entry.get("request_params"), value_map)
            entry["request_body"] = self._replace_values(entry.get("request_body"), value_map)
            entry["request_headers"] = self._replace_values(entry.get("request_headers"), value_map)

        return entries, variable_rules, conflicts

    def _is_dynamic_key(self, key):
        lower = key.lower()
        return any(keyword in lower for keyword in self.DYNAMIC_KEYWORDS)

    def _replace_values(self, data, value_map):
        if isinstance(data, dict):
            return {
                key: self._replace_values(value, value_map)
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [self._replace_values(item, value_map) for item in data]
        for key, (target_value, variable_name) in value_map.items():
            if data == target_value:
                return f"${{{variable_name}}}"
        return data
