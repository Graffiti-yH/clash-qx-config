# Clash / Quantumult X 网络配置

面向中国大陆使用场景的个人网络配置仓库：

- Mac：Clash
- iPhone：优先 Clash，Quantumult X 作为备用
- 中国大陆网站、App、银行支付、公司内网、游戏、局域网：直连
- AI：美国节点
- X / Instagram：日本节点
- YouTube：台湾或香港节点
- 其他海外流量：全部国家节点自动选择
- 节点不可用时：阻断，不回退直连
- DNS：国内外分流 + 加密 DNS + DNS 广告拦截

> 本仓库为公开仓库。真实订阅链接、节点信息、密码和 Token **不得**写入仓库。

## 目录

```text
Clash/                 Clash/Mihomo 配置模板
Quantumult X/          Quantumult X 配置模板
规则/Clash/            Clash 规则提供商文件
规则/Quantumult X/     Quantumult X 过滤规则文件
文档/                   网络拓扑、待办和维护说明
```

## 直接导入规则

将 `Graffiti-yH/clash-qx-config` 替换为仓库实际地址：

```text
https://raw.githubusercontent.com/Graffiti-yH/clash-qx-config/main/规则/Clash/人工智能.list
https://raw.githubusercontent.com/Graffiti-yH/clash-qx-config/main/规则/Clash/社交软件.list
https://raw.githubusercontent.com/Graffiti-yH/clash-qx-config/main/规则/Clash/流媒体.list
https://raw.githubusercontent.com/Graffiti-yH/clash-qx-config/main/规则/Clash/中国大陆直连.list
https://raw.githubusercontent.com/Graffiti-yH/clash-qx-config/main/规则/Clash/局域网直连.list
https://raw.githubusercontent.com/Graffiti-yH/clash-qx-config/main/规则/Clash/哔哩哔哩直连.list
https://raw.githubusercontent.com/Graffiti-yH/clash-qx-config/main/规则/Clash/广告拦截.list
```

Quantumult X 使用对应目录中的同名文件。

## 使用原则

1. 先在 Clash 或 Quantumult X 的应用界面添加订阅。
2. 再导入本仓库中的规则文件或配置模板。
3. AI、社交、流媒体策略组只筛选目标国家节点，不会跨国家自动跳转。
4. “其他海外—自动”允许在全部国家节点中测速选择。
5. `MATCH` / 未匹配海外流量进入“其他海外—自动”；节点不可用时阻断。
6. iPhone 同时只能启用 Clash 或 Quantumult X 其中一个 VPN 隧道。

## 重要安全说明

- 公开仓库只存规则与模板。
- 订阅 URL 可能包含完整访问权限，不能提交到 GitHub。
- MITM/重写暂不作为默认配置；只有明确需要时再在 Quantumult X 中单独启用，并排除银行、支付、微信、QQ 等敏感 App。
- 本仓库不配置路由器，不作为局域网网关。

## 提取原始订阅链接

如果服务商给的是订阅转换链接，可以使用：

```bash
python3 工具/提取纯订阅链接.py
```

然后粘贴转换链接并回车。脚本会隐藏输入，并只输出解码后的原始 `url` 参数。

也可以从本地文件读取：

```bash
python3 工具/提取纯订阅链接.py --文件 ~/Downloads/转换链接.txt
```

订阅链接包含访问凭据，结果只能保存在本地，不能提交到公开仓库。

## 官方资料

- [Clash for Apple Platforms](https://clash.md/)
- [Clash iOS](https://clash.md/platforms/ios)
- [Clash macOS](https://clash.md/platforms/macos)
- [Quantumult X 官方主页](https://quantumult.app/x/)
- [Quantumult X 官方 GitHub](https://github.com/crossutility/Quantumult-X)
- [Quantumult X Rewrite 示例](https://github.com/crossutility/Quantumult-X/blob/master/rewrite.md)
- [Otty](https://otty.sh/)

## 进度

详见 [待办清单.md](文档/待办清单.md)。
