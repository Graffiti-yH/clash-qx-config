#!/usr/bin/env python3
"""从公开模板生成只保存在本机的 Clash 配置。

订阅地址使用隐藏输入，不会显示在终端，也不会写入 GitHub 模板。
"""

from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path
from urllib.parse import urlparse


根目录 = Path(__file__).resolve().parents[1]
模板 = 根目录 / "Clash" / "配置模板.yaml"
输出 = 根目录 / "Clash" / "配置-本地.yaml"
占位符 = 'url: "请在本地替换为真实订阅链接"'


def main() -> int:
    if 输出.exists():
        确认 = input(f"{输出} 已存在，是否覆盖？[y/N] ").strip().lower()
        if 确认 != "y":
            print("已取消")
            return 0

    订阅地址 = getpass.getpass("粘贴服务商 Clash 订阅链接（不会回显）：").strip()
    地址 = urlparse(订阅地址)
    if 地址.scheme not in {"http", "https"} or not 地址.netloc:
        print("错误：不是有效的 HTTP/HTTPS 订阅链接", file=sys.stderr)
        return 1

    内容 = 模板.read_text(encoding="utf-8")
    if 占位符 not in 内容:
        print("错误：模板中找不到订阅地址占位符", file=sys.stderr)
        return 1

    输出.write_text(内容.replace(占位符, f'url: "{订阅地址}"', 1), encoding="utf-8")
    os.chmod(输出, 0o600)
    print(f"已生成本地配置：{输出}")
    print("请将这个文件导入 Clash；以后在 Clash 内更新代理提供商和规则提供商。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
