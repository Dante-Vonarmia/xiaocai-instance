# 云鹤AI接入采购中国小程序术语表

文档状态：配套术语说明  
日期：2026-06-12

## 1. 术语与推荐命名

| 中文口径 | 推荐英文/字段名 | 说明 |
| --- | --- | --- |
| 小程序内嵌登录 | Mini Program WebView SSO | 采购中国小程序通过 web-view 内嵌云鹤AI并自动完成身份进入 |
| 单点登录 | SSO / Single Sign-On | 用户已登录采购中国后，无需再次输入账号、密码或短信验证码即可进入云鹤AI |
| URL 授权参数 | URL Authorization Parameter | 小程序打开云鹤AI时通过 URL 携带的参数 |
| 短期一次性登录凭证 | Short-lived One-time Login Credential | URL 参数值，短期有效、建议一次性使用 |
| 登录票据 | Login Ticket | 推荐参数语义，可作为 URL 参数名使用 |
| SSO 票据 | SSO Ticket | 偏 SSO 场景的票据命名 |
| 授权码 | Authorization Code | 如果采购中国已有 OAuth/授权码体系，可沿用该命名 |
| 登录凭证校验接口 | Credential Verification API | 云鹤AI后端调用采购中国后端，用于校验登录凭证并换取用户信息 |
| 服务端校验 | Server-to-Server Verification | 云鹤AI后端到采购中国后端的校验，不由浏览器前端直接调用 |
| 凭证换取用户身份 | Credential Exchange | 云鹤AI用登录凭证换取当前采购中国用户身份 |
| 本地登录态 | Local Application Session | 云鹤AI校验成功后建立的自身登录态 |
| 会话 Cookie | Session Cookie | 云鹤AI可用于维持本地登录态的 Cookie |
| 一次性使用 | Single-use / One-time Use | 登录凭证校验成功后立即失效 |
| 有效期 | TTL / Expiration Time | 登录凭证有效时间，建议 1-5 分钟 |
| 防重放 | Replay Protection | 防止同一登录凭证或同一签名请求被重复使用 |
| 随机不可预测 | Cryptographically Random / Unguessable | 登录凭证应随机生成，不能由用户ID或手机号拼接 |
| 绑定用户 | Subject Binding | 登录凭证绑定当前采购中国登录用户 |
| 绑定应用 | Audience Binding / Client Binding | 登录凭证绑定云鹤AI应用标识 |
| 应用标识 | Client ID / App ID | 采购中国分配给云鹤AI的应用标识，如 `yunhe_ai` |
| 接口签名 | Request Signature | 校验接口请求签名，用于证明请求来自云鹤AI后端 |
| 时间戳 | Timestamp | 校验接口签名字段之一，用于限制请求时间窗口 |
| 随机串 | Nonce | 校验接口签名字段之一，用于防重放 |
| IP 白名单 | IP Allowlist | 采购中国侧可限制只允许云鹤AI服务器出口 IP 调用校验接口 |
| 外部访问拦截 | External Access Blocking | 外部直接打开云鹤AI且无有效登录态时不允许进入业务页面 |

推荐 URL 参数名：

```text
login_ticket
```

备选参数名：

```text
sso_ticket
auth_code
```

如采购中国已有统一登录、SSO 或 OAuth 接入规范，可优先沿用其既有参数名和接口命名。本文档中使用 `login_ticket` 作为推荐示例名。
