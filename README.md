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
https://raw.githubusercontent.com/Graffiti-yH/clash-qx-config/main/规则/Clash/广告拦截.list
```

Quantumult X 使用对应目录中的同名文件。

## 统一更新

推荐使用“一个本地配置外壳 + 远程订阅 + 远程规则提供商”的方式。只需一次性配置，之后可在 Clash 内分别更新节点和分流规则，无需反复导入本地文件。详见 [统一更新方案.md](文档/统一更新方案.md)。

## 使用原则

1. 不要把服务商下发的完整配置作为唯一活动配置，否则会使用服务商自带分流规则。
2. 一次性使用本仓库配置模板作为活动配置，并把服务商链接只填写到 `proxy-providers.订阅节点.url`；这样只读取节点，不使用服务商的 rules、dns 和 proxy-groups。
3. AI、社交、流媒体策略组只筛选目标国家节点，不会跨国家自动跳转。
4. “其他海外—自动”允许在全部国家节点中测速选择。
5. `MATCH` / 未匹配海外流量进入“其他海外—自动”；节点不可用时阻断。
6. iPhone 同时只能启用 Clash 或 Quantumult X 其中一个 VPN 隧道。

## 重要安全说明

- 公开仓库只存规则与模板。
- 订阅 URL 可能包含完整访问权限，不能提交到 GitHub。
- MITM/重写暂不作为默认配置；只有明确需要时再在 Quantumult X 中单独启用，并排除银行、支付、微信、QQ 等敏感 App。
- 本仓库不配置路由器，不作为局域网网关。

## 无订阅纯分流配置

Clash 纯分流配置（不包含订阅链接和节点）：

```text
https://raw.githubusercontent.com/Graffiti-yH/clash-qx-config/main/Clash/%E7%BA%AF%E5%88%86%E6%B5%81%E9%85%8D%E7%BD%AE.yaml
```

该配置的策略组会自动接收后续通过“覆写”加入的节点。

## 生成本地 Clash 配置

服务商链接不要直接作为活动配置。推荐只执行一次：

```bash
python3 工具/生成本地Clash配置.py
```

脚本会隐藏输入订阅地址，生成被 Git 忽略的 `Clash/配置-本地.yaml`。将它导入 Clash 后，节点和分流规则都可以在 Clash 内更新。

## 本地订阅转换器

在不把订阅地址发送给第三方的前提下，将服务商链接转换为本地 Clash 覆写节点和协议链接：

```bash
python3 工具/本地订阅转换器.py
```

然后在浏览器打开 `http://127.0.0.1:8765`。程序默认只监听本机，订阅地址只保存在内存中。若要让同一局域网手机直接订阅，启动时加上：

```bash
python3 工具/本地订阅转换器.py --局域网 --地址 192.168.1.100
```

将 `192.168.1.100` 换成 Mac 的局域网 IP；网页生成的临时 `/sub/.../clash.yaml` 地址即可粘贴到手机 Clash。手机和 Mac 必须在同一局域网，程序运行期间不能关闭终端。

它会生成：

- `覆写节点.yaml`：包含全部原协议节点，适合 Clash 覆写
- `全部协议链接.txt`：保留 `ss://`、`vmess://`、`trojan://` 等原协议

Trojan 不能安全转换成 SS/VMess，因此保留为 `trojan://`，不会排除。

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
