# mq-novels-hooks

用于小说创作工作流的 Claude Code hooks。在 Claude Code 会话中自动运行，强制执行项目规范、防止误操作。

## Hooks 一览

### novel-path-validator.py

**触发事件：** `PreToolUse` (Write / Edit / MultiEdit)

校验文件写入路径是否符合小说项目的目录结构：

```
{NOVELS_ROOT}/{类型}/{主角}/{项目名}/{顶层目录}/...
```

- 允许的顶层目录：`book/`、`s0_chapters/`、`s1_info/`、`s3_images/`
- 通过 `book/config.json` 锚点判断项目是否已建立
- 项目名拼写错误时自动提示相似项目名
- 从脚本位置自动推导 `NOVELS_ROOT`，无需配置环境变量

### agent-guard.py

**触发事件：** `PreToolUse` (Agent)

Agent 调用白名单守卫。只放行 `agent-allowlist.json` 中匹配的任务描述，未授权的 Agent 调用会被拦截（exit 2）。

### chapter-outline-reminder.py

**触发事件：** `PreToolUse` (Write)

当写入目标路径包含 `chapter-outlines/` 时，向模型上下文注入提醒：
> 确认你正在按顺序逐章生成。写完本章后，必须先确认写入成功，再开始生成下一章。禁止在内存中预先生成多章内容。

不阻止写入（exit 0），仅通过 stdout 注入提醒信息。

## 配置文件

### agent-allowlist.json

授权的 Agent 任务描述正则表达式。编辑此文件来增减允许的 Agent 任务：

```json
{
  "allowed_patterns": [
    "^第\\d+幕写作（章\\d+-\\d+）$",
    "^分镜切分$",
    ...
  ]
}
```

## 安装使用

1. 将本仓库克隆到小说工作区的 `.claude/hooks/` 目录：
   ```bash
   git clone https://github.com/mikeshuangyan/mq-novels-hooks.git /path/to/novels/.claude/hooks
   ```

2. 在 Claude Code 的 `settings.json` 中添加 hook 配置（完整示例见 [settings.example.json](settings.example.json)）：
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Write|Edit|MultiEdit",
           "hooks": [{ "type": "command", "command": "python3 /path/to/novels/.claude/hooks/novel-path-validator.py" }]
         }
       ]
     }
   }
   ```

3. 将 `/path/to/novels/` 替换为你的实际小说根目录路径。

## Hook 工作机制

| 退出码 | 行为 |
|--------|------|
| 0 | 放行 — 工具调用正常执行 |
| 2 | 拦截 — 工具调用被阻止，stderr 信息展示给模型 |

- **stdout** → 注入模型上下文（用于提醒信息）
- **stderr** → 拦截时作为错误信息展示（exit 2）
