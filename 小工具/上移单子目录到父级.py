# -*- coding: utf-8 -*-
"""
将“内嵌只有一个文件夹”的目录结构上移到父目录（默认只处理一层）。

两种使用方式：
1) 批量模式（默认）：遍历指定路径下的所有子目录，如果某子目录中只有一个子文件夹，则将该子文件夹上移到指定路径，并删除空的包裹目录。
   示例：python 小工具/上移单子目录到父级.py d:\\path\\to\\root

2) 自身模式（--self）：如果指定路径自身只包含一个子文件夹，则将该子文件夹上移到“指定路径”的父目录，并删除原目录。
   示例：python 小工具/上移单子目录到父级.py d:\\path\\to\\target --self

仅处理一层，不做递归。遇到目标重名时安全跳过。
"""

import argparse
import shutil
import sys
from pathlib import Path


def find_single_subdir(dir_path: Path):
    """若目录中只有一个条目且该条目是文件夹，则返回该子文件夹 Path，否则返回 None。"""
    try:
        entries = list(dir_path.iterdir())
    except Exception:
        return None

    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return None


def process_children(parent_path: Path, dry_run: bool = False):
    """批量处理：遍历 parent_path 下所有子目录，满足条件则上移一层。"""
    moved_count = 0
    skipped_count = 0
    error_count = 0

    for child in parent_path.iterdir():
        if not child.is_dir():
            continue

        inner = find_single_subdir(child)
        if inner is None:
            continue

        dest = parent_path / inner.name

        if dest.exists():
            print(f"[跳过] 目标已存在，避免重名：{dest}")
            skipped_count += 1
            continue

        print(f"[移动] {inner} -> {dest}")
        if dry_run:
            moved_count += 1
            continue

        try:
            shutil.move(str(inner), str(dest))
            try:
                child.rmdir()
                print(f"[删除] 空目录：{child}")
            except OSError:
                print(f"[保留] 目录非空或删除失败：{child}")
            moved_count += 1
        except Exception as e:
            print(f"[错误] 移动失败：{inner} -> {dest}，原因：{e}")
            error_count += 1

    print(f"\n完成：移动 {moved_count}，跳过 {skipped_count}，错误 {error_count}")


def process_self(path: Path, dry_run: bool = False):
    """自身模式：若 path 只包含一个子文件夹，则上移到父目录。"""
    inner = find_single_subdir(path)
    if inner is None:
        print(f"[跳过] 指定路径不是单子目录结构：{path}")
        return

    parent_path = path.parent
    dest = parent_path / inner.name

    if dest.exists():
        print(f"[跳过] 目标已存在，避免重名：{dest}")
        return

    print(f"[移动] {inner} -> {dest}")
    if dry_run:
        return

    try:
        shutil.move(str(inner), str(dest))
        try:
            path.rmdir()
            print(f"[删除] 空目录：{path}")
        except OSError:
            print(f"[保留] 目录非空或删除失败：{path}")
    except Exception as e:
        print(f"[错误] 移动失败：{inner} -> {dest}，原因：{e}")


def main():
    parser = argparse.ArgumentParser(
        description="将内嵌只有一个文件夹的结构上移到父目录（只处理一层）",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="要处理的目录路径；默认当前目录",
    )
    parser.add_argument(
        "--self",
        action="store_true",
        help="仅处理自身（若自身只有一个子文件夹则上移到父目录）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="演示模式：只显示将执行的操作，不实际移动/删除",
    )

    args = parser.parse_args()
    target = Path(args.path).resolve()

    if not target.exists() or not target.is_dir():
        print(f"[错误] 目标路径不存在或不是目录：{target}")
        sys.exit(1)

    if args.self:
        process_self(target, dry_run=args.dry_run)
    else:
        process_children(target, dry_run=args.dry_run)


if __name__ == "__main__":
    main()