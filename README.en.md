# organize-markdown-images

[English](README.en.md) | [简体中文](README.md)

A [Claude Code](https://claude.com/claude-code) Skill that tidies up image references in Markdown documents.

## Features

Scans `.md` files for image references, copies scattered local images into a single `图片/<document-title>/` directory, renames them sequentially as `01-`, `02-`…, and rewrites the Markdown references to relative paths. The processed document and its images can then be uploaded to a web/blog platform as a unit.

> Note: the output folder is named `图片` (Chinese for "images") — this is hardcoded in the script so that Chinese filenames sort correctly alongside the document.

- ✅ Scans both Markdown `![](…)` and HTML `<img>` references
- ✅ Sequential numbering (`01-xxx.png`, `02-yyy.png`)
- ✅ Filenames derived from alt text or the original filename (Unicode preserved)
- ✅ Resolves relative, absolute, and `file:///` paths
- ✅ Web image URLs are left untouched (not downloaded)
- ✅ Missing images are reported without aborting the run
- ✅ Idempotent: already-organized references are skipped, safe to re-run

## Repository layout

```
organize-markdown-images-skill/
├── SKILL.md                       # Claude Code Skill entry (frontmatter + docs)
├── scripts/
│   └── organize_images.py         # Core script (stdlib only, no third-party deps)
└── evals/
    └── evals.json                 # Evaluation cases
```

## Use as a plain script

```bash
python scripts/organize_images.py <markdown-file-or-directory>
```

Options:

- `--no-overwrite`: do not overwrite when the destination already exists (overwrites by default)

On completion, a Markdown report is printed to stdout listing, for every image of every file, its original path / new path / status.

## Install as a Claude Code Skill

Copy `SKILL.md`, `scripts/`, and `evals/` into your Claude Code skills directory:

- Windows: `C:\Users\<you>\.claude\skills\organize-markdown-images\`
- macOS / Linux: `~/.claude/skills/organize-markdown-images/`

Then in Claude Code, say something like "tidy up the images in the markdown docs under this directory" and the Skill will be triggered automatically.

## Example

Before:

```markdown
![login](assets/screenshot.png)
![architecture](/home/user/diagram.png)
![online](https://example.com/sample.png)
```

After (for a file named `My Doc.md`):

```markdown
![login](图片/My Doc/01-login.png)
![architecture](图片/My Doc/02-architecture.png)
![online](https://example.com/sample.png)
```

## License

MIT
