# GitHub SSH 连接配置

**日期:** 2026-03-05  
**状态:** ⚠️ 需要用户操作

---

## 已完成 (自动)

- [x] 创建 `~/.ssh/` 目录
- [x] 生成 SSH 密钥对 (`~/.ssh/id_rsa` + `~/.ssh/id_rsa.pub`)
- [x] 创建 SSH config (使用 443 端口)
- [x] 添加 GitHub 主机密钥到 `known_hosts`

---

## 需要用户操作

### 1. 添加公钥到 GitHub

**公钥内容:**
```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCa8jdkcnjxxPwxuTDYxYVbhdFEaSjJkr4kDrzno8tOi/Aj8iTf2q2IURPCmBXEb01wCoSbU1TXRt1g2POB6NI9qxo1T00eOrtx6NPG7uJ5o5JtMmla+3K37KtDB2PbgQB3aF5q9rN80vui6cCtjSRZ8TrEiAPDL+GxnTDWquqwZ3DPnOjTAmpHZRoa3jwtofIAOhuaEzyGv0GbBT/HSQUNDbQiB+7iF6S+Y8xSgX3hhYg+Ltu34EYZj+vrkIUsla6FwS+i5pCwSZNecCQYlw5+5m3xbuF4R2jv0T7fcgTpxVvryzaPiZBiPoLaZCwS/lSw4K8pJfMwAON7mLkzlqwD+6vgMv8umWLBtQugz424FVv4dMjVc7EDeTclWGYl6dJIhV1WzCxvwv6qSiuNW4Fm9M+FViwRh+CX43fmvljb9SMuhN2jd9+OkyfyMu5wICSVam4PU7RgfKxP1/XljHtDNOOWLH3O7pXRo9YnnnPPk4k1C8tRjn1XX98fZezSzjCpwzFkaZKbfUAFOCMpcmrRzMgvW6/hr+WqvWJFPt4w6lj82jNPjnTYlRt1/HWCVqrNiXog7LbnYUNCRcfg5MCN4guVe8tc5KwRuwp0GSDUJBQU7xU4fX0BZUOvOnezGFkGcoHsg4TgQNoiLQta6T1gepq1jYZANGIMQVNQbo3Khw== openclaw@localhost
```

**操作步骤:**
1. 复制上述公钥
2. 访问 https://github.com/settings/keys
3. 点击 "New SSH key"
4. 粘贴公钥，标题填写 "OpenClaw@DESKTOP-196SGOR"
5. 点击 "Add SSH key"

### 2. 验证连接

添加公钥后，执行以下命令验证：
```bash
ssh -T git@github.com
```

**成功输出:**
```
Hi AIIS188! You've successfully authenticated, but GitHub does not provide shell access.
```

---

## SSH Config 配置

文件位置：`~/.ssh/config`

```
Host github.com
    HostName ssh.github.com
    Port 443
    User git
    IdentityFile ~/.ssh/id_rsa
    TCPKeepAlive yes
    ServerAliveInterval 30
```

**说明:**
- 使用 443 端口 (HTTPS) 绕过防火墙
- 启用保活机制防止连接超时

---

## 更新后的 install-skill.sh

脚本已更新为 **SSH 优先** 策略：

```bash
# 优先使用 SSH (更稳定，不受速率限制)
git clone git@github.com:owner/repo.git

# 降级使用 HTTPS (当 SSH 不可用时)
git clone https://github.com/owner/repo.git
```

---

## 为什么使用 SSH？

| 对比项 | HTTPS | SSH |
|--------|-------|-----|
| 认证方式 | Token/密码 | 密钥对 |
| 超时问题 | 常见 | 较少 |
| 速率限制 | 有 | 无 |
| 防火墙穿透 | 差 | 好 (443 端口) |
| 长期稳定性 | 一般 | 优秀 |

---

## 故障排除

### 问题 1: Permission denied (publickey)
**原因:** 公钥未添加到 GitHub  
**解决:** 完成上述用户操作步骤

### 问题 2: Connection timed out
**原因:** 网络问题或防火墙  
**解决:** SSH config 已配置 443 端口，如仍失败检查网络

### 问题 3: Host key verification failed
**原因:** known_hosts 缺失或错误  
**解决:** 已自动添加，如仍有问题执行：
```bash
rm ~/.ssh/known_hosts
ssh-keyscan -H github.com >> ~/.ssh/known_hosts
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `~/.ssh/id_rsa` | 私钥 (勿分享) |
| `~/.ssh/id_rsa.pub` | 公钥 (添加到 GitHub) |
| `~/.ssh/config` | SSH 配置 |
| `~/.ssh/known_hosts` | 主机密钥 |
| `scripts/install-skill.sh` | Skill 安装脚本 (已更新为 SSH 优先) |

---

**下一步:** 添加公钥到 GitHub 后，执行 `ssh -T git@github.com` 验证
