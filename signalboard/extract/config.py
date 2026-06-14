"""signalboard.extract 集中配置(模型名、provider 切换、默认参数等)。

升级 LLM 模型或换 provider 时改这里,不要散落在 caller.py / scripts 各处。
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# LLM Provider
# ---------------------------------------------------------------------------

PROVIDER = "deepseek"   # 本次用 deepseek;可切 "anthropic" / "deepseek"

# 支持的 provider 列表(测试时校验)
SUPPORTED_PROVIDERS = ("anthropic", "deepseek")


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------

ANTHROPIC_BASE_URL = "https://api.anthropic.com"
ANTHROPIC_MODEL = "claude-sonnet-4-6"     # 2026-06:spec v1.0 写的 4-5 已过时,Anthropic 已是 4.6
ANTHROPIC_VERSION = "2023-06-01"


# ---------------------------------------------------------------------------
# DeepSeek
# ---------------------------------------------------------------------------

DEEPSEEK_BASE_URL = "https://api.deepseek.com"   # OpenAI 兼容
# 注意:deepseek-chat 已弃用,改用 v4 系列
#   - deepseek-v4-flash:轻量,速度优先
#   - deepseek-v4-pro:质量优先(默认)
DEEPSEEK_MODEL = "deepseek-v4-pro"

# 思考模式控制(spec 第 5 节:抽取是规则判定,不需要推理链,关闭思考)
DEEPSEEK_THINKING = {"type": "disabled"}

# 强制 JSON 输出(DeepSeek 文档要求 prompt 含 "json" 字面量)
DEEPSEEK_RESPONSE_FORMAT = {"type": "json_object"}


# ---------------------------------------------------------------------------
# 当前 active 模型(根据 PROVIDER 选)
# ---------------------------------------------------------------------------

ACTIVE_MODEL = DEEPSEEK_MODEL if PROVIDER == "deepseek" else ANTHROPIC_MODEL
ACTIVE_BASE_URL = DEEPSEEK_BASE_URL if PROVIDER == "deepseek" else ANTHROPIC_BASE_URL
# key 环境变量名
ACTIVE_KEY_ENV = "DEEPSEEK_API_KEY" if PROVIDER == "deepseek" else "ANTHROPIC_API_KEY"


# ---------------------------------------------------------------------------
# 通用 LLM 调用参数
# ---------------------------------------------------------------------------

LLM_MAX_TOKENS = 8192  # 30 条清单场景,4096 还不够,提 8192           # 30 条清单场景,1024 偏紧
LLM_TEMPERATURE = 0.0           # 规则判定,可复现
LLM_MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# 缓存
# ---------------------------------------------------------------------------

# 缓存 key 用 provider + model + prompt_version 三元组
# (不同 provider/model 输出不可混用)
def get_cache_key_tag(prompt_version: str = "v1.1") -> str:
    """用于 extraction_cache 的 (post_id, prompt_version) 第二个字段。

    把 provider+model 编进 prompt_version,自动按 provider/model 隔离缓存。
    prompt_version 跟 signalboard.extract.prompts.PROMPT_VERSION 同步(手动)。
    """
    return f"{PROVIDER}:{ACTIVE_MODEL}:{prompt_version}"


# 跟 prompts.PROMPT_VERSION 同步 — 改这里时也要改 prompts.PROMPT_VERSION
CACHE_KEY_PROMPT_VERSION = get_cache_key_tag("v1.4.1")
