#!/usr/bin/env python3
"""从订阅转换链接中提取并解码原始订阅链接。

用法：
    python3 工具/提取纯订阅链接.py
    python3 工具/提取纯订阅链接.py --链接 '转换链接'
    python3 工具/提取纯订阅链接.py --文件 /path/to/转换链接.txt

默认使用隐藏输入，避免订阅链接出现在终端回显中。
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


def 提取(转换链接: str) -> tuple[str, str | None]:
    转换链接 = 转换链接.strip()
    if not 转换链接:
        raise ValueError("转换链接为空")

    parsed = urlparse(转换链接)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("不是有效的 HTTP/HTTPS 链接")

    参数 = parse_qs(parsed.query, keep_blank_values=True)
    原始参数 = 参数.get("url")
    if not 原始参数 or not 原始参数[0].strip():
        raise ValueError("链接中没有找到 url 参数")

    # parse_qs 已经解码一次；再处理一层兼容双重编码链接。
    纯订阅链接 = 原始参数[0].strip()
    for _ in range(2):
        解码后 = unquote(纯订阅链接)
        if 解码后 == 纯订阅链接:
            break
        纯订阅链接 = 解码后

    订阅地址 = urlparse(纯订阅链接)
    if 订阅地址.scheme not in {"http", "https"} or not 订阅地址.netloc:
        raise ValueError("url 参数解码后不是有效的 HTTP/HTTPS 订阅链接")

    target = 参数.get("target", [None])[0] or None
    return 纯订阅链接, target


def main() -> int:
    parser = argparse.ArgumentParser(description="提取订阅转换链接中的原始订阅地址")
    parser.add_argument("--链接", help="转换链接；命令行参数可能进入 shell 历史记录")
    parser.add_argument("--文件", type=Path, help="包含转换链接的本地文件")
    parser.add_argument("--保存", type=Path, help="将结果保存到本地文件（不要放入公开仓库）")
    args = parser.parse_args()

    if args.链接 and args.文件:
        print("错误：--链接 和 --文件只能使用一个", file=sys.stderr)
        return 2

    try:
        if args.链接:
            转换链接 = args.链接
        elif args.文件:
            转换链接 = args.文件.read_text(encoding="utf-8")
        else:
            转换链接 = getpass.getpass("粘贴转换链接（输入不会回显）：")

        纯订阅链接, target = 提取(转换链接)
        if target:
            print(f"转换目标：{target}", file=sys.stderr)
        print(纯订阅链接)

        if args.保存:
            args.保存.write_text(纯订阅链接 + "\n", encoding="utf-8")
            print(f"已保存到：{args.保存}", file=sys.stderr)
        return 0
    except (OSError, ValueError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
