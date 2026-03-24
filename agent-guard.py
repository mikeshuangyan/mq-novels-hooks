#!/usr/bin/env python3
"""
Agent 调用白名单 Hook（PreToolUse: Agent）

只放行 allowlist 中匹配的 description，其余一律拦截。
白名单文件：与本脚本同目录下的 agent-allowlist.json
"""

import json
import os
import re
import sys


def load_allowlist():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "agent-allowlist.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["allowed_patterns"]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name") != "Agent":
        sys.exit(0)

    description = data.get("tool_input", {}).get("description", "")

    try:
        patterns = load_allowlist()
    except Exception as e:
        # 白名单文件读取失败时放行，避免阻塞整个流程
        print(
            f"[agent-guard] ⚠️ 无法读取白名单文件，放行: {e}",
            file=sys.stderr,
        )
        sys.exit(0)

    for pattern in patterns:
        if re.search(pattern, description):
            # 匹配白名单，放行
            sys.exit(0)

    # 不匹配，拦截——消息需明确：仅此 description 被拦截，不影响后续步骤中授权的 Agent
    allowed_list = ", ".join(patterns)
    print(
        f"[agent-guard] ❌ 未授权的 Agent 调用已被拦截\n"
        f"  被拦截的 description: {description!r}\n"
        f"  原因：该 description 不在白名单中。\n"
        f"  当前白名单：{allowed_list}\n"
        f"\n"
        f"  处理方式：将本次被拦截的任务在当前上下文中内联执行。\n"
        f"  重要提示：本次拦截仅针对上述 description。后续步骤如果指令文件中要求启动 Agent，\n"
        f"  且该 Agent 的 description 在白名单中，仍然必须正常启动，不得因本次拦截而跳过。",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
