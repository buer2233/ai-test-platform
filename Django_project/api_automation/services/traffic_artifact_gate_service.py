"""
生成用例门禁服务

负责试运行结果写入与状态流转。
"""


class ArtifactGateService:
    """试运行门禁处理。"""

    def apply_trial_result(self, artifact, passed, error_info=None):
        if passed:
            artifact.status = "READY"
        else:
            artifact.status = "DRAFT"
            preview = artifact.preview_diff or {}
            preview["error_info"] = error_info or "试运行失败"
            artifact.preview_diff = preview
        return artifact
