# organize-markdown-images

[简体中文](README.md) | [English](README.en.md)

一个 [Claude Code](https://claude.com/claude-code) Skill：整理 Markdown 文档中的图片引用。

## 功能

扫描 `.md` 文件中的图片引用，把分散在各处的本地图片统一复制到 `图片/<文档标题>/` 目录下，按出现顺序重命名为 `01-`、`02-`…，并把 markdown 里的引用更新为相对路径。处理完的文档连同图片可以直接整体上传到网页/博客系统。

- ✅ 自动扫描 Markdown 与 HTML `<img>` 图片引用
- ✅ 按出现顺序编号（`01-xxx.png`、`02-yyy.png`）
- ✅ 文件名来自 alt 文本或原文件名（保留中文）
- ✅ 相对路径、绝对路径、`file:///` 均可解析
- ✅ 网络图片 URL 保持原样不下载
- ✅ 缺失图片在报告中列出，不会中断流程
- ✅ 幂等：已规范化的引用自动跳过，可重复运行

## 目录结构

```
organize-markdown-images-skill/
├── SKILL.md                       # Claude Code Skill 入口（frontmatter + 说明）
├── scripts/
│   └── organize_images.py         # 核心处理脚本（无第三方依赖，标准库）
└── evals/
    └── evals.json                 # 评估用例
```

## 直接当脚本用

```bash
python scripts/organize_images.py <markdown文件或目录>
```

可选参数：

- `--no-overwrite`：目标文件已存在时不覆盖（默认会覆盖）

处理完成会在标准输出打印一份 Markdown 报告，列出每个文件每张图的 原路径 / 新路径 / 状态。

## 作为 Claude Code Skill 安装

把 `SKILL.md`、`scripts/`、`evals/` 复制到 Claude Code 的 skills 目录：

- Windows：`C:\Users\<你>\.claude\skills\organize-markdown-images\`
- macOS / Linux：`~/.claude/skills/organize-markdown-images/`

之后在 Claude Code 里说"整理这个目录下 markdown 文档的图片"，该 Skill 会被自动触发。

## 行为示例

处理前：

```markdown
![登录界面](assets/screenshot.png)
![架构图](/home/user/diagram.png)
![在线图](https://example.com/sample.png)
```

处理后：

```markdown
![登录界面](图片/文档标题/01-登录界面.png)
![架构图](图片/文档标题/02-架构图.png)
![在线图](https://example.com/sample.png)
```

## 许可

MIT
