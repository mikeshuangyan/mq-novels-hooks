#!/usr/bin/env python3
"""
Sleep 轮询拦截 Hook（PreToolUse: Bash）

拦截所有包含 `sleep` 的 Bash 命令，阻止 Agent 用 sleep 轮询后台任务。
"""

import json
import re
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")

    # 匹配 sleep 命令：sleep 后跟数字（秒数）
    if not re.search(r"\bsleep\s+\d+", command):
        sys.exit(0)

    # 拦截
    print(
        "[sleep-guard] ❌ 检测到 sleep 命令，已拦截。\n"
        "\n"
        "  被拦截的命令: " + command[:300] + "\n"
        "\n"
        "  ===== 原因 =====\n"
        "\n"
        "  你用 Bash(run_in_background=true) 启动了一个后台任务，然后试图用\n"
        "  sleep 等待一段时间再手动检查输出。这是错误的。\n"
        "\n"
        "  ===== 正确机制 =====\n"
        "\n"
        "  Bash(run_in_background=true) 启动的任务，完成后系统会自动向你发送\n"
        "  一条通知消息，包含任务的完整输出。你不需要做任何事来获取结果。\n"
        "\n"
        "  ===== 立即执行 =====\n"
        "\n"
        "  停止一切 sleep / 轮询 / 手动读取 output 文件的尝试。\n"
        "  等待系统自动发送的后台任务完成通知，收到后再继续处理。\n"
        "\n"
        "  ===== 以下所有变体均被本 hook 拦截 =====\n"
        "\n"
        "  - sleep N && cat output\n"
        "  - sleep N; cat output\n"
        "  - sleep N && tail output\n"
        "  - sleep N; kill $PID; cat output\n"
        "  - while/for 循环 + sleep\n"
        "  - 任何包含 sleep 的 Bash 命令\n",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
