#!/usr/bin/env python3
"""
小说文件路径校验 Hook（PreToolUse: Write|Edit）

NOVELS_ROOT 自动从脚本位置推导：
  脚本位于 $NOVELS_ROOT/.claude/hooks/novel-path-validator.py

路径结构：$NOVELS_ROOT/{genre}/{protagonist}/{project}/{known_dir}/{rest}

项目名校验：以 book/config.json 为锚点判断项目是否已建立。
"""

import difflib
import json
import os
import re
import sys


# 从脚本自身位置推导 NOVELS_ROOT，无需环境变量
# 脚本路径：$NOVELS_ROOT/.claude/hooks/novel-path-validator.py
_hooks_dir = os.path.dirname(os.path.abspath(__file__))   # .claude/hooks/
_claude_dir = os.path.dirname(_hooks_dir)                  # .claude/
NOVELS_ROOT = os.path.dirname(_claude_dir).rstrip("/")     # $NOVELS_ROOT


# ── 合法路径规则（按顶层目录分类）────────────────────────────────────────

BOOK_PATTERNS = [
    r"^config\.json$",
    r"^progress\.json$",
    r"^00-剧情草案\.md$",
    r"^01-世界观\.md$",
    r"^02-大纲\.md$",
    r"^03-人物档案\.md$",
    r"^04-场景档案\.md$",
    r"^05-写作风格\.md$",
    r"^06-全局伏笔追踪\.md$",
    r"^chapter-outlines/chapter\d+\.md$",
    r"^chapters/chapter\d+\.md$",
]

S0_PATTERNS = [
    r"^s0_original/b\d+_chapter\d+\.txt$",
]

STORYBOARD_DRAFT_FILES = {
    "meta.json",
    "numbered.txt",
    "registry.json",
    "segments.txt",
    "details.json",
    "draft.json",
    "patches.txt",
    "violations.json",
}
STORYBOARD_DRAFT_CHUNK_PATTERN = re.compile(
    r"^chunk\d+(?:\.details)?(?:\.json|\.txt)$"
)

S1_FIXED_FILES = {
    "characters.json",
    "location.json",
    "genre.txt",
    "metadata.txt",
}
STORYBOARD_FINAL_PATTERN = re.compile(r"^storyboard/b\d+_chapter\d+\.json$")
CHAPTER_NAME_PATTERN = re.compile(r"^b\d+_chapter\d+$")


# ── 项目名校验（以 config.json 为锚点）───────────────────────────────────

def check_project_via_config(genre, protagonist, project, known_dir, rest):
    """
    用 book/config.json 是否存在来判断项目是否已建立。

    - 写 book/config.json 本身：无条件放行（建立项目的操作）
    - 其他文件：若 config.json 存在则放行；否则在同级查找已建立的相似项目名
      - 有相似 → 阻断并提示
      - 无相似 → 视为新项目，放行
    """
    # book/config.json 无条件放行（建立项目）
    if known_dir == "book" and rest == "config.json":
        return True, None

    config_path = os.path.join(
        NOVELS_ROOT, genre, protagonist, project, "book", "config.json"
    )
    if os.path.isfile(config_path):
        return True, None  # 项目已建立，放行

    # config.json 不存在，项目未初始化，直接报错
    # 顺带查找相似项目名作为提示
    parent = os.path.join(NOVELS_ROOT, genre, protagonist)
    established = []
    if os.path.isdir(parent):
        try:
            for d in os.listdir(parent):
                if os.path.isfile(os.path.join(parent, d, "book", "config.json")):
                    established.append(d)
        except OSError:
            pass

    hint = ""
    if established:
        similar = difflib.get_close_matches(project, established, n=3, cutoff=0.5)
        if similar:
            hint = "\n是否写错了项目名？相似的已建立项目：\n" + "\n".join(f"  {s}" for s in similar)
        else:
            hint = "\n该路径下已建立的项目：\n" + "\n".join(f"  {e}" for e in established)

    return False, (
        f"项目 {project!r} 未找到 book/config.json（项目未初始化）{hint}"
    )


# ── 文件路径格式校验 ──────────────────────────────────────────────────────

def validate_book(rest):
    for pattern in BOOK_PATTERNS:
        if re.match(pattern, rest):
            return True, None
    return False, (
        f"book/ 下路径不合法: {rest!r}\n"
        "合法示例：\n"
        "  book/config.json\n"
        "  book/progress.json\n"
        "  book/00-剧情草案.md … 05-写作风格.md\n"
        "  book/chapter-outlines/chapter01.md\n"
        "  book/chapters/chapter01.md"
    )


def validate_s0(rest):
    for pattern in S0_PATTERNS:
        if re.match(pattern, rest):
            return True, None
    return False, (
        f"s0_chapters/ 下路径不合法: {rest!r}\n"
        "合法示例：s0_chapters/s0_original/b1_chapter01.txt"
    )


def validate_s1(rest):
    if rest in S1_FIXED_FILES:
        return True, None

    if STORYBOARD_FINAL_PATTERN.match(rest):
        return True, None

    if rest.startswith("storyboard_draft/"):
        inner = rest[len("storyboard_draft/"):]
        parts = inner.split("/", 1)
        if len(parts) == 2:
            chapter_dir, filename = parts
            if CHAPTER_NAME_PATTERN.match(chapter_dir):
                if filename in STORYBOARD_DRAFT_FILES:
                    return True, None
                if STORYBOARD_DRAFT_CHUNK_PATTERN.match(filename):
                    return True, None
        return False, (
            f"s1_info/storyboard_draft/ 下路径不合法: {rest!r}\n"
            "合法示例：\n"
            "  s1_info/storyboard_draft/b1_chapter01/meta.json\n"
            "  s1_info/storyboard_draft/b1_chapter01/chunk1.txt\n"
            "  s1_info/storyboard_draft/b1_chapter01/chunk1.details.json"
        )

    return False, (
        f"s1_info/ 下路径不合法: {rest!r}\n"
        "合法示例：\n"
        "  s1_info/characters.json\n"
        "  s1_info/location.json\n"
        "  s1_info/storyboard/b1_chapter01.json\n"
        "  s1_info/storyboard_draft/b1_chapter01/draft.json"
    )


def validate_path(file_path):
    """返回 (is_valid, error_message)"""
    prefix = NOVELS_ROOT + "/"
    if not file_path.startswith(prefix):
        return True, None  # 非小说路径，放行

    rel = file_path[len(prefix):]
    parts = rel.split("/")

    if len(parts) < 4:
        return False, (
            f"路径层级不足（需要 genre/主角/项目名/顶层目录/...）: {file_path}"
        )

    genre, protagonist, project, known_dir = (
        parts[0], parts[1], parts[2], parts[3]
    )
    rest = "/".join(parts[4:])

    if not rest:
        return False, f"路径缺少具体文件名: {file_path}"

    # 先用 config.json 锚点校验项目名
    ok, err = check_project_via_config(genre, protagonist, project, known_dir, rest)
    if not ok:
        return False, err

    if known_dir == "book":
        return validate_book(rest)
    elif known_dir == "s0_chapters":
        return validate_s0(rest)
    elif known_dir == "s1_info":
        return validate_s1(rest)
    else:
        return False, (
            f"未知顶层目录 {known_dir!r}，只允许 s0_chapters / s1_info / book\n"
            f"路径: {file_path}"
        )


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    is_valid, error_msg = validate_path(file_path)
    if not is_valid:
        print(
            f"[novel-path-validator] 路径校验失败，已阻止写入\n{error_msg}",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
