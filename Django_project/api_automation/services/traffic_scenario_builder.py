"""
流量场景拼接服务

将过滤后的流量条目拼接为可执行步骤。
"""


class TrafficScenarioBuilder:
    """根据时间序列构建场景步骤。"""

    def build(self, entries):
        steps = []
        requires_manual_confirmation = False

        for index, entry in enumerate(entries, start=1):
            if not entry.get("is_valuable", True) or entry.get("response_status") is None:
                requires_manual_confirmation = True

            steps.append({
                "step_order": index,
                "name": f"{entry.get('request_method') or 'REQUEST'} {entry.get('request_url') or ''}",
                "request": {
                    "method": entry.get("request_method"),
                    "url": entry.get("request_url"),
                    "headers": entry.get("request_headers") or {},
                    "params": entry.get("request_params") or {},
                    "body": entry.get("request_body") or {},
                },
                "assertions": [
                    {
                        "assertion_type": "status_code",
                        "operator": "equals",
                        "expected_value": entry.get("response_status") or 200,
                    }
                ],
                "response_status": entry.get("response_status"),
            })

        return {
            "steps": steps,
            "requires_manual_confirmation": requires_manual_confirmation,
        }
