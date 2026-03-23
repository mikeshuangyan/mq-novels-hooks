#!/usr/bin/env python3
"""
章节大纲逐章写入提醒 Hook（PreToolUse: Write）

当 Write 目标路径包含 chapter-outlines/ 时，输出提醒（stdout → 模型可见）。
不阻止写入（exit 0），仅注入提醒信息。
"""

import json
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name") != "Write":
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")

    if "chapter-outlines/" not in file_path:
        sys.exit(0)

    # 提醒注入（stdout → 模型可见）
    print(
        "⚠️ 逐章写入提醒：确认你正在按顺序逐章生成。"
        "写完本章后，必须先确认写入成功，再开始生成下一章。"
        "禁止在内存中预先生成多章内容。"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
