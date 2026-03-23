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

    # 不匹配，拦截
    print(
        f"[agent-guard] ❌ 未授权的 Agent 调用已被拦截\n"
        f"  description: {description!r}\n"
        f"  该任务未在步骤文件中授权委托给 Agent。\n"
        f"  请重新阅读当前步骤的指令文件，在自己的上下文中内联执行该任务，不要委托给子 Agent。",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
