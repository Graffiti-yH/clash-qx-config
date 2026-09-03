#!/usr/bin/env python3
"""本地订阅转换器：默认只在 127.0.0.1 运行，不保存订阅地址。

使用 --局域网 后，可让同一局域网内的手机通过临时 token 订阅生成的配置。

用途：把 Clash YAML/常见 Base64 订阅转换为：
- Clash 覆写片段（proxies: ...）
- 全部协议链接（包含 ss://、vmess://、trojan://）

Trojan 节点不能安全地伪装成 SS/VMess，因此保留为 trojan://，不强行转换或排除。
"""

from __future__ import annotations

import base64
import binascii
import html
import ipaddress
import json
import secrets
import socket
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

根目录 = Path(__file__).resolve().parents[1]
最大响应 = 10 * 1024 * 1024
输出缓存: dict[str, dict[str, bytes | int]] = {}
缓存锁 = threading.Lock()
公开地址 = "http://127.0.0.1:8765"
监听说明 = "127.0.0.1（仅本机）"


def 解码_base64(value: str) -> bytes:
    value = "".join(value.split())
    value += "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value.encode())


def 解析_clash_yaml(data: bytes) -> list[dict]:
    """使用 macOS 自带 Ruby Psych 安全解析 Clash YAML。"""
    import subprocess

    ruby = r'''
require "yaml"
require "json"
begin
  x = YAML.safe_load(STDIN.read, [], [], true)
  proxies = x.is_a?(Hash) ? x["proxies"] : nil
  puts JSON.generate(proxies.is_a?(Array) ? proxies : [])
rescue StandardError
  puts "[]"
end
'''
    try:
        result = subprocess.run(
            ["ruby", "-e", ruby],
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
        )
        value = json.loads(result.stdout.decode("utf-8", "replace"))
        return [x for x in value if isinstance(x, dict)]
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def 解析_uri_lines(text: str) -> list[dict]:
    nodes: list[dict] = []
    for raw in text.splitlines():
        uri = raw.strip()
        if not uri:
            continue
        try:
            if uri.startswith("vmess://"):
                payload = 解码_base64(uri[8:].split("#", 1)[0]).decode("utf-8")
                item = json.loads(payload)
                nodes.append({
                    "name": item.get("ps") or item.get("add") or "VMess",
                    "type": "vmess",
                    "server": item.get("add"),
                    "port": int(item.get("port", 443)),
                    "uuid": item.get("id"),
                    "alterId": int(item.get("aid", 0)),
                    "cipher": item.get("scy", "auto"),
                    "tls": str(item.get("tls", "")).lower() in {"tls", "true", "1"},
                    "network": item.get("net", "tcp"),
                    "servername": item.get("sni") or item.get("host"),
                    "ws-opts": {"path": item.get("path", "/"), "headers": {"Host": item.get("host")}}
                    if item.get("net") == "ws" else None,
                })
            elif uri.startswith("ss://"):
                parsed = urllib.parse.urlsplit(uri)
                name = urllib.parse.unquote(parsed.fragment or "SS")
                user = parsed.username
                password = parsed.password
                host = parsed.hostname
                port = parsed.port
                if host and password is None and user:
                    # SIP002 格式：base64(method:password)@host:port
                    try:
                        decoded_auth = 解码_base64(user).decode()
                        user, password = decoded_auth.split(":", 1)
                    except (UnicodeError, ValueError, binascii.Error):
                        pass
                if not host:
                    decoded = 解码_base64(parsed.path.lstrip("/")).decode()
                    auth, hostport = decoded.rsplit("@", 1)
                    user, password = auth.split(":", 1)
                    host, port_text = hostport.rsplit(":", 1)
                    port = int(port_text)
                nodes.append({"name": name, "type": "ss", "server": host, "port": port,
                              "cipher": urllib.parse.unquote(user or ""),
                              "password": urllib.parse.unquote(password or "")})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError, binascii.Error):
            continue
    return nodes


def 获取节点(url: str) -> list[dict]:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("只允许 HTTP/HTTPS 订阅地址")
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain", "metadata.google.internal"}:
        raise ValueError("不允许访问本机或云元数据地址")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("不允许访问内网地址")
    except ValueError as exc:
        if str(exc) == "不允许访问内网地址":
            raise

    request = urllib.request.Request(url, headers={
        "User-Agent": "Local-Clash-Converter/1.0",
        "Accept": "application/yaml,text/yaml,text/plain,*/*",
    })
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read(最大响应 + 1)
    except Exception as exc:
        raise ValueError(f"订阅获取失败：{exc}") from exc
    if len(body) > 最大响应:
        raise ValueError("订阅响应超过 10 MB，已拒绝处理")

    nodes = 解析_clash_yaml(body)
    if not nodes:
        text = body.decode("utf-8", "replace")
        nodes = 解析_uri_lines(text)
    if not nodes:
        try:
            decoded = 解码_base64(body.decode("utf-8"))
            nodes = 解析_clash_yaml(decoded) or 解析_uri_lines(decoded.decode("utf-8", "replace"))
        except (UnicodeError, binascii.Error, ValueError):
            pass
    if not nodes:
        raise ValueError("未识别到 Clash 节点或 ss/vmess 节点")
    return [清理节点(x) for x in nodes if x.get("server") and x.get("port")]


def 清理节点(node: dict) -> dict:
    out = {}
    for key, value in node.items():
        if value is None or value == "":
            continue
        if key in {"name", "type", "server", "port", "uuid", "alterId", "cipher", "password",
                   "tls", "network", "servername", "ws-opts", "grpc-opts", "sni", "skip-cert-verify"}:
            out[key] = value
    return out


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def 节点转链接(node: dict) -> str | None:
    typ = str(node.get("type", "")).lower()
    name = urllib.parse.quote(str(node.get("name", "节点")), safe="")
    server = node.get("server")
    port = node.get("port")
    if not server or not port:
        return None
    if typ in {"ss", "shadowsocks"}:
        auth = f"{node.get('cipher', '')}:{node.get('password', '')}".encode()
        return f"ss://{b64(auth)}@{server}:{port}#{name}"
    if typ == "vmess":
        ws = node.get("ws-opts") or {}
        headers = ws.get("headers") or {}
        payload = {
            "v": "2", "ps": node.get("name", "VMess"), "add": server,
            "port": str(port), "id": node.get("uuid", ""),
            "aid": str(node.get("alterId", 0)), "scy": node.get("cipher", "auto"),
            "net": node.get("network", "tcp"), "type": "none",
            "host": headers.get("Host", ""), "path": ws.get("path", "/"),
            "tls": "tls" if node.get("tls") else "",
            "sni": node.get("servername") or node.get("sni", ""),
        }
        return "vmess://" + base64.b64encode(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()).decode()
    if typ == "trojan":
        query = {}
        if node.get("sni") or node.get("servername"):
            query["sni"] = node.get("sni") or node.get("servername")
        query_text = urllib.parse.urlencode(query)
        return f"trojan://{urllib.parse.quote(str(node.get('password', '')), safe='')}@{server}:{port}?{query_text}#{name}"
    return None


def 代理_yaml(nodes: list[dict]) -> bytes:
    rows = ["# 本地生成的 Clash 节点片段；不包含服务商订阅地址\nproxies:"]
    for node in nodes:
        rows.append("  - " + json.dumps(node, ensure_ascii=False, separators=(",", ":")))
    return ("\n".join(rows) + "\n").encode("utf-8")


def 完整_clash_yaml(nodes: list[dict]) -> bytes:
    """把节点插入纯分流配置，生成可被 Clash 直接订阅的完整配置。"""
    template = (根目录 / "Clash" / "纯分流配置.yaml").read_text(encoding="utf-8")
    rows = ["# 本地生成的 Clash 配置；节点来自本次转换，分流规则来自 GitHub\nproxies:"]
    for node in nodes:
        rows.append("  - " + json.dumps(node, ensure_ascii=False, separators=(",", ":")))
    return ("\n".join(rows) + "\n" + template).encode("utf-8")


def 页面(message: str = "", token: str = "") -> bytes:
    result = ""
    if message:
        result = f'<div class="result">{html.escape(message)}</div>'
    downloads = ""
    if token:
        局域网订阅 = f'''<div class="downloads">
<a href="/download/{token}/覆写节点.yaml">下载 Clash 覆写节点.yaml</a>
<a href="/download/{token}/全部协议链接.txt">下载全部协议链接.txt（含 Trojan）</a>
</div><h3>局域网订阅地址</h3><p class="hint">将下面地址粘贴到同一局域网手机的 Clash 中：</p><div class="result">{html.escape(公开地址)}/sub/{token}/clash.yaml</div>'''
        downloads = 局域网订阅
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>本地订阅转换器</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:760px;margin:48px auto;padding:0 20px;color:#222}}input{{width:100%;box-sizing:border-box;padding:12px;font-size:16px;margin:8px 0 14px}}button{{padding:10px 18px;font-size:16px}}.hint{{color:#666;line-height:1.6}}.result{{margin-top:20px;padding:14px;background:#f1f7ff;border-radius:8px;white-space:pre-wrap;overflow-wrap:anywhere}}.downloads{{display:grid;gap:10px;margin-top:20px}}a{{color:#06c}}</style>
<h1>本地订阅转换器</h1><p class="hint">{html.escape(监听说明)}。订阅地址只在本机处理，不保存到磁盘、不发送到第三方。服务商链接会被请求一次。</p>
<form method="post" action="/generate"><label>服务商 Clash 订阅链接</label><input type="url" name="url" required autocomplete="off" placeholder="https://..."><button type="submit">生成本地配置</button></form>{result}{downloads}
<p class="hint">说明：Trojan 不能伪装成 SS/VMess，程序会保留为 trojan://；完整 Clash 配置和覆写 YAML 都会保留 Trojan。</p></html>'''.encode("utf-8")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(页面())
            return
        parts = urllib.parse.urlsplit(self.path).path.strip("/").split("/")
        if len(parts) == 3 and parts[0] in {"download", "sub"}:
            token, filename = parts[1], urllib.parse.unquote(parts[2])
            文件名 = filename
            if parts[0] == "sub":
                文件名 = {"clash.yaml": "clash.yaml", "proxies.yaml": "覆写节点.yaml", "links.txt": "全部协议链接.txt"}.get(filename, "")
            with 缓存锁:
                item = 输出缓存.get(token)
            if item and 文件名 in item:
                data = item[文件名]
                content_type = "text/yaml; charset=utf-8" if filename.endswith("yaml") else "text/plain; charset=utf-8"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)  # type: ignore[arg-type]
                return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/generate":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length > 8192:
            self.send_error(413, "订阅地址过长")
            return
        body = self.rfile.read(length)
        params = urllib.parse.parse_qs(body.decode("utf-8", "replace"))
        url = (params.get("url") or [""])[0].strip()
        try:
            nodes = 获取节点(url)
            links = [x for x in (节点转链接(n) for n in nodes) if x]
            token = secrets.token_urlsafe(12)
            files: dict[str, bytes | int] = {
                "clash.yaml": 完整_clash_yaml(nodes),
                "覆写节点.yaml": 代理_yaml(nodes),
                "全部协议链接.txt": ("\n".join(links) + "\n").encode(),
                "count": len(nodes),
            }
            with 缓存锁:
                输出缓存.clear()
                输出缓存[token] = files
            msg = f"已识别 {len(nodes)} 个节点；已生成覆写 YAML 和全部协议链接（含 Trojan）。"
            data = 页面(msg, token)
            self.send_response(200)
        except ValueError as exc:
            data = 页面(str(exc))
            self.send_response(400)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    import argparse
    import subprocess

    parser = argparse.ArgumentParser(description="本地订阅转换器")
    parser.add_argument("--端口", type=int, default=8765)
    parser.add_argument("--局域网", action="store_true", help="允许同一局域网设备访问")
    parser.add_argument("--地址", help="局域网订阅地址中显示的 Mac IP；不填则自动检测")
    args = parser.parse_args()

    global 公开地址, 监听说明
    if args.局域网:
        bind = "0.0.0.0"
        display_ip = args.地址
        if not display_ip:
            for interface in ("en0", "en1"):
                try:
                    display_ip = subprocess.check_output(
                        ["ipconfig", "getifaddr", interface], stderr=subprocess.DEVNULL,
                        text=True, timeout=2,
                    ).strip()
                    if display_ip:
                        break
                except (OSError, subprocess.SubprocessError):
                    pass
        display_ip = display_ip or "请替换为 Mac 局域网 IP"
        公开地址 = f"http://{display_ip}:{args.端口}"
        监听说明 = "监听所有网卡（仅建议在可信家庭局域网使用）"
    else:
        bind = "127.0.0.1"
        公开地址 = f"http://127.0.0.1:{args.端口}"
        监听说明 = "仅监听 127.0.0.1"

    server = ThreadingHTTPServer((bind, args.端口), Handler)
    print(f"本地订阅转换器已启动：{公开地址}")
    print("按 Ctrl+C 停止；不会打印或保存订阅地址。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
