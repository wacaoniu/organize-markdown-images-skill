#!/usr/bin/env python3
"""
整理 Markdown 文档中的图片引用。

扫描 markdown 文件中的图片引用，把图片复制到统一图片目录并按顺序重命名，
最后改为相对路径，方便上传网页文档。
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

# 确保 Windows 终端下输出中文不乱码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def find_markdown_files(target: Path) -> list[Path]:
    """查找目标路径下的所有 markdown 文件。"""
    if target.is_file() and target.suffix.lower() == ".md":
        return [target]
    return sorted(target.rglob("*.md"))


def extract_image_refs(content: str) -> list[tuple[str, str, int, int]]:
    """
    提取 markdown 和 HTML 中的图片引用。

    返回: [(完整匹配, 图片路径, 开始位置, 结束位置), ...]
    """
    results = []

    # Markdown 图片: ![alt](path)
    md_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    for match in md_pattern.finditer(content):
        results.append((match.group(0), match.group(2), match.start(), match.end()))

    # HTML 图片: <img src="path" ...>
    html_pattern = re.compile(r"<img[^>]+src\s*=\s*['\"]([^'\"]+)['\"][^>]*>", re.IGNORECASE)
    for match in html_pattern.finditer(content):
        results.append((match.group(0), match.group(1), match.start(), match.end()))

    # 按位置排序
    results.sort(key=lambda x: x[2])
    return results


def normalize_image_path(path: str) -> str:
    """统一路径分隔符为正斜杠。"""
    return path.replace("\\", "/")


def resolve_image_path(doc_dir: Path, image_path: str) -> Path | None:
    """
    根据文档目录解析图片的真实路径。

    支持相对路径和绝对路径。
    """
    image_path = unquote(image_path).strip()
    image_path = image_path.replace("file:///", "")

    if os.path.isabs(image_path):
        return Path(image_path)

    return (doc_dir / image_path).resolve()


def is_web_url(path: str) -> bool:
    """判断是否为网络图片 URL。"""
    return path.lower().startswith(("http://", "https://"))


def sanitize_filename(name: str) -> str:
    """
    清理文件名，移除非法字符。

    保留中文字符和常见字符。
    """
    name = re.sub(r'[<>:"/\\|?*\s]+', "-", name)
    name = name.strip("-.")
    return name if name else "image"


def build_new_filename(order: int, alt_text: str, original_path: str) -> str:
    """根据编号、alt 文本和原文件名构建新文件名。"""
    suffix = Path(original_path).suffix
    if not suffix:
        suffix = ".png"  # 默认扩展名

    source_name = Path(original_path).stem
    name_part = sanitize_filename(alt_text) if alt_text else sanitize_filename(source_name)
    return f"{order:02d}-{name_part}{suffix}"


def process_markdown_file(md_file: Path, overwrite: bool = True) -> dict:
    """处理单个 markdown 文件，返回处理结果。"""
    doc_dir = md_file.parent
    doc_title = md_file.stem
    target_dir = doc_dir / "图片" / doc_title

    content = md_file.read_text(encoding="utf-8")
    image_refs = extract_image_refs(content)

    results = {
        "file": str(md_file),
        "copied": 0,
        "missing": 0,
        "skipped": 0,
        "web": 0,
        "images": [],
    }

    if not image_refs:
        return results

    target_dir.mkdir(parents=True, exist_ok=True)

    # 从后往前替换，避免位置偏移
    replacements = []
    order = 0

    for full_match, image_path, start, end in image_refs:
        normalized_path = normalize_image_path(image_path)

        if is_web_url(normalized_path):
            results["web"] += 1
            results["images"].append({
                "original": normalized_path,
                "new": normalized_path,
                "status": "web_url_unchanged",
            })
            continue

        # 如果已经是目标目录内的相对路径，跳过
        expected_prefix = f"图片/{doc_title}/"
        if normalized_path.startswith(expected_prefix):
            results["skipped"] += 1
            results["images"].append({
                "original": normalized_path,
                "new": normalized_path,
                "status": "already_organized",
            })
            continue

        order += 1
        src_path = resolve_image_path(doc_dir, normalized_path)

        if not src_path or not src_path.exists():
            results["missing"] += 1
            results["images"].append({
                "original": normalized_path,
                "new": None,
                "status": "missing",
            })
            continue

        # 提取 alt 文本
        alt_text = ""
        md_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", full_match)
        if md_match:
            alt_text = md_match.group(1)

        new_filename = build_new_filename(order, alt_text, str(src_path))
        dest_path = target_dir / new_filename

        if dest_path.exists() and not overwrite:
            results["images"].append({
                "original": normalized_path,
                "new": str(dest_path.relative_to(doc_dir)).replace("\\", "/"),
                "status": "exists_not_overwritten",
            })
            continue

        shutil.copy2(src_path, dest_path)
        results["copied"] += 1

        relative_new = str(dest_path.relative_to(doc_dir)).replace("\\", "/")
        results["images"].append({
            "original": normalized_path,
            "new": relative_new,
            "status": "copied",
        })

        # 构建新的引用
        if md_match:
            new_ref = f"![{alt_text}]({relative_new})"
        else:
            # HTML 形式，仅替换 src
            new_ref = full_match.replace(image_path, relative_new)

        replacements.append((start, end, new_ref))

    # 从后往前替换内容
    for start, end, new_ref in reversed(replacements):
        content = content[:start] + new_ref + content[end:]

    md_file.write_text(content, encoding="utf-8")
    return results


def format_report(results: list[dict]) -> str:
    """格式化输出报告。"""
    total_files = len(results)
    total_copied = sum(r["copied"] for r in results)
    total_missing = sum(r["missing"] for r in results)
    total_skipped = sum(r["skipped"] for r in results)
    total_web = sum(r["web"] for r in results)

    lines = [
        "## 处理结果摘要",
        "",
        f"- 处理的 Markdown 文件数：{total_files}",
        f"- 复制的图片数：{total_copied}",
        f"- 缺失或无法处理的图片数：{total_missing}",
        f"- 已规范化跳过的图片数：{total_skipped}",
        f"- 网络图片数（保持原样）：{total_web}",
        "",
        "### 文件详情",
        "",
    ]

    for r in results:
        lines.append(f"#### {r['file']}")
        lines.append("")
        lines.append("| 原路径 | 新路径 | 状态 |")
        lines.append("|--------|--------|------|")
        for img in r["images"]:
            original = img["original"]
            new_path = img["new"] if img["new"] else "—"
            status = img["status"]
            lines.append(f"| {original} | {new_path} | {status} |")
        lines.append("")

    lines.extend([
        "### 注意事项",
        "",
        "- 图片编号按出现顺序从 01 开始。",
        "- 目标目录中的图片已按规则重命名，如果原文件已存在则被覆盖。",
        "- 网络图片 URL 保持原样，未进行下载。",
        "- 请检查缺失的图片，确保引用的文件路径正确。",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="整理 Markdown 文档中的图片引用"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="要处理的 markdown 文件或目录（默认：当前目录）",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="目标文件已存在时不覆盖",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"错误：目标路径不存在：{target}", file=sys.stderr)
        sys.exit(1)

    md_files = find_markdown_files(target)
    if not md_files:
        print("未找到 Markdown 文件。", file=sys.stderr)
        sys.exit(0)

    results = []
    for md_file in md_files:
        result = process_markdown_file(md_file, overwrite=not args.no_overwrite)
        results.append(result)

    print(format_report(results))


if __name__ == "__main__":
    main()
