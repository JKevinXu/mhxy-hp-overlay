from dataclasses import dataclass

FORBIDDEN_TERMS = (
    "memory",
    "packet",
    "protocol reverse",
    "inject",
    "hook",
    "hidden state",
    "auto input",
    "adb input",
    "auto click",
    "bot",
    "bypass",
    "anti-cheat bypass",
    "内存",
    "封包",
    "抓包",
    "注入",
    "隐藏状态",
    "自动点击",
    "自动战斗",
    "脚本输入",
)

ALLOWED_TERMS = (
    "screenshot",
    "screen recording",
    "visible",
    "authorized",
    "image",
    "video",
    "manual roi",
    "可见",
    "截图",
    "录屏",
    "手动",
    "屏幕",
)


@dataclass(frozen=True)
class ComplianceDecision:
    allowed: bool
    reason: str


def check_feature_scope(description: str) -> ComplianceDecision:
    text = description.lower()
    for term in FORBIDDEN_TERMS:
        if term.lower() in text:
            return ComplianceDecision(False, f"forbidden direction: {term}")
    if any(term.lower() in text for term in ALLOWED_TERMS):
        return ComplianceDecision(True, "compliant visible-screen analysis direction")
    return ComplianceDecision(False, "scope unclear; require explicit visible/authorized media source")
