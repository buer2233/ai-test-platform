"""
流量过滤服务

负责静态资源、探活请求过滤以及去重。
"""

import hashlib
import json


class TrafficFilterService:
    """流量过滤与去重。"""

    STATIC_EXTENSIONS = (".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico")
    HEALTH_KEYWORDS = ("/health", "/ping", "/status")

    def filter_entries(self, entries):
        filtered = []
        fingerprints = set()
        stats = {
            "filtered_count": 0,
            "deduplicated_count": 0,
        }

        for entry in entries:
            entry = dict(entry)
            entry.setdefault("is_valuable", True)

            url = entry.get("request_url") or ""
            if url.lower().endswith(self.STATIC_EXTENSIONS):
                entry["is_valuable"] = False
                entry["filter_reason"] = "STATIC_RESOURCE"
            if any(keyword in url.lower() for keyword in self.HEALTH_KEYWORDS):
                entry["is_valuable"] = False
                entry["filter_reason"] = "HEALTH_CHECK"

            fingerprint = self._fingerprint(entry)
            if fingerprint in fingerprints:
                entry["is_valuable"] = False
                entry["filter_reason"] = "DUPLICATE"
                stats["deduplicated_count"] += 1
            else:
                fingerprints.add(fingerprint)

            if not entry.get("is_valuable", True):
                stats["filtered_count"] += 1

            entry["fingerprint"] = fingerprint
            filtered.append(entry)

        return filtered, stats

    def _fingerprint(self, entry):
        payload = {
            "method": entry.get("request_method"),
            "url": entry.get("request_url"),
            "params": entry.get("request_params") or {},
            "body": entry.get("request_body") or {},
        }
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
