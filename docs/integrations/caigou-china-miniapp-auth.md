# 云鹤AI × 采购中国小程序会员登录接入规范

文档状态：云鹤AI侧实现与联调规范  
适用范围：`https://yunheai.cloud/` 现有地址挂载采购中国小程序 `web-view`  
关联需求：OPS-51

## 1. 接入目标

采购中国小程序已登录用户通过 `web-view` 打开云鹤AI时，云鹤AI完成身份识别并建立本地登录态。外部直接访问、无效凭证、过期凭证和不可用账号不得进入业务页面。

本期只做会员登录与访问拦截，不做会员表同步、订单同步、供应商同步或独立新入口。

## 2. 总体链路

```text
采购中国小程序已登录用户
  -> 点击云鹤AI入口
  -> 采购中国生成短期登录凭证 ticket
  -> 小程序 web-view 打开 https://yunheai.cloud/?ticket={login_ticket}
  -> 云鹤AI前端读取 ticket 并调用云鹤AI后端 /auth/exchange
  -> 云鹤AI后端调用采购中国凭证校验接口
  -> 校验成功后生成云鹤AI本地 JWT 登录态
  -> 前端清理 URL 中的 ticket
  -> 用户进入云鹤AI业务页面
```

外部访问链路：

```text
直接打开 https://yunheai.cloud/
  -> 无 ticket
  -> 无云鹤AI本地登录态
  -> 拦截并提示从采购中国小程序进入
```

## 3. 云鹤AI入口地址

生产地址：

```text
https://yunheai.cloud/?ticket={login_ticket}
```

本地验证地址：

```text
http://localhost:23001/?ticket=test
```

云鹤AI当前兼容以下 URL 参数名，推荐双方统一使用 `ticket`：

```text
ticket
login_ticket
token
credential
sso_ticket
auth_code
```

URL 中不得携带手机号、用户ID、会员等级等明文业务信息。

## 4. 采购中国侧需提供

| 类别 | 内容 |
| --- | --- |
| 小程序 web-view | 确认可打开 `https://yunheai.cloud/`，并配置业务域名 |
| 域名校验 | 如微信要求校验文件，提供文件内容；云鹤AI放置到站点根目录 |
| ticket 生成 | 生成时机、有效期、是否一次性、是否绑定用户、是否绑定云鹤AI应用 |
| 校验接口 | 接口地址、请求方式、请求字段、返回字段、错误码 |
| 接口鉴权 | appId、appSecret 或等价鉴权方式；是否要求 IP 白名单 |
| 测试资料 | 测试小程序入口、测试账号、有效/无效/过期/已使用 ticket 样例 |

当前云鹤AI已放置的域名校验文件：

```text
/fLWSO3QWD6.txt
```

上线后应能访问：

```text
https://yunheai.cloud/fLWSO3QWD6.txt
```

## 5. ticket 要求

| 项目 | 要求 |
| --- | --- |
| 类型 | 短期登录凭证，建议一次性使用 |
| 有效期 | 建议 1-5 分钟 |
| 随机性 | 随机、不可预测，不能由用户ID或手机号拼接 |
| 绑定对象 | 当前采购中国登录用户 |
| 绑定应用 | 云鹤AI应用标识，如 `yunhe_ai` |
| 明文信息 | 不包含手机号、用户ID、会员等级等业务字段 |
| 使用方式 | 只用于登录交换，不作为后续 API token |

## 6. 采购中国凭证校验接口

请求方向：

```text
云鹤AI后端 -> 采购中国后端
```

该接口不能由浏览器前端直接调用。

### 6.1 推荐请求格式

```json
{
  "appId": "yunhe_ai",
  "credential": "ticket_value",
  "timestamp": 1710000000,
  "nonce": "random_string",
  "signature": "HMAC_SHA256(appId + credential + timestamp + nonce, appSecret)"
}
```

如果采购中国已有既定签名或网关鉴权规范，以采购中国规范为准；云鹤AI侧通过 provider 适配，不把上游细节扩散到路由或前端。

### 6.2 成功响应

```json
{
  "valid": true,
  "user": {
    "id": "316",
    "name": "韩经伟",
    "status": "active",
    "mobile": "176****1134",
    "openid": "optional_openid",
    "unionid": "optional_unionid"
  }
}
```

云鹤AI必需字段：

| 字段 | 必填 | 用途 |
| --- | --- | --- |
| `id` 或 `user_id` | 是 | 外部用户唯一标识 |
| `name` / `nickname` / `display_name` | 是 | 页面展示当前用户 |
| `status` | 是 | 判断账号是否可进入 |

手机号、openid、unionid 为可选字段。本期云鹤AI不要求存储手机号明文。

### 6.3 失败响应

```json
{
  "valid": false,
  "error": "CREDENTIAL_EXPIRED",
  "message": "登录凭证已过期"
}
```

采购中国建议错误码：

```text
CREDENTIAL_MISSING
CREDENTIAL_INVALID
CREDENTIAL_EXPIRED
CREDENTIAL_USED
USER_DISABLED
SIGNATURE_INVALID
APP_UNAUTHORIZED
VERIFY_FAILED
```

云鹤AI会将上游错误码映射为稳定产品提示，不直接把上游原始异常或 Python exception 展示给用户。

## 7. 云鹤AI本地 JWT 登录态

采购中国只负责证明 ticket 对应的用户身份。云鹤AI校验成功后生成自己的 JWT，本地 API 只认：

```http
Authorization: Bearer <xiaocai_access_token>
```

JWT 最小 claims：

```json
{
  "sub": "316",
  "source": "caigou_china",
  "external_user_id": "316",
  "display_name": "韩经伟",
  "member_status": "active",
  "roles": ["user"],
  "iat": "issued_at",
  "exp": "expires_at",
  "last_login_at": "login_time"
}
```

JWT 不包含：

```text
ticket
appSecret
手机号明文
订单/供应商/会员等级等业务敏感信息
```

## 8. 错误码与用户提示

云鹤AI `/auth/exchange` 失败响应结构：

```json
{
  "detail": {
    "code": "CREDENTIAL_EXPIRED",
    "message": "登录已过期，请返回采购中国小程序重新进入"
  }
}
```

| code | HTTP | 用户提示 |
| --- | --- | --- |
| `CREDENTIAL_MISSING` | 401 | 请从采购中国小程序进入云鹤AI服务 |
| `CREDENTIAL_INVALID` | 401 | 登录凭证无效，请返回采购中国小程序重新进入 |
| `CREDENTIAL_EXPIRED` | 401 | 登录已过期，请返回采购中国小程序重新进入 |
| `CREDENTIAL_USED` | 401 | 登录凭证已失效，请重新进入 |
| `USER_DISABLED` | 403 | 当前账号状态不可用，请联系采购中国客服 |
| `VERIFY_TIMEOUT` | 503 | 登录服务暂时不可用，请稍后重试 |
| `VERIFY_FAILED` | 503 | 登录服务暂时不可用，请稍后重试 |
| `CONFIG_MISSING` | 500 | 云鹤AI登录服务配置异常，请联系管理员 |
| `SIGNATURE_INVALID` | 502 | 云鹤AI登录服务配置异常，请联系管理员 |
| `APP_UNAUTHORIZED` | 502 | 云鹤AI登录服务暂未获得授权，请联系管理员 |
| `RESPONSE_INVALID` | 502 | 登录服务暂时不可用，请稍后重试 |

产品界面展示 `message`。日志记录 `code` 与必要的排障信息，但不得记录完整 ticket 或 appSecret。

## 9. 日志与排障规范

云鹤AI认证链路至少应能定位以下事件：

```text
auth_exchange_success
auth_exchange_failed
credential_invalid
credential_expired
credential_used
user_disabled
verify_timeout
verify_failed
api_unauthorized
```

日志建议字段：

```text
request_id
source=caigou_china
auth_error_code
external_user_id
upstream_latency_ms
ticket_hash
```

禁止记录：

```text
完整 ticket
appSecret
手机号明文
```

## 10. 安全配置建议

必需：

```text
微信/小程序 web-view 业务域名配置
服务端 ticket 校验
云鹤AI本地 JWT 登录态
后端 API Bearer token 鉴权
生产环境关闭 mock 登录
```

建议：

```text
appId + appSecret 签名
timestamp + nonce 防重放
HTTPS
固定出口 IP 时增加 IP 白名单
```

IP 白名单不是强制前置条件。如果云鹤AI部署环境没有固定出口 IP，可先以签名鉴权为主。

## 11. 云鹤AI部署配置

生产环境建议：

```env
MOCK_AUTH=false
VITE_ENABLE_MOCK_AUTH=false
INSTANCE_JWT_SECRET=replace-with-strong-secret
CAIGOU_CHINA_AUTH_VERIFY_URL=https://采购中国校验接口
CAIGOU_CHINA_APP_ID=yunhe_ai
CAIGOU_CHINA_APP_SECRET=通过安全渠道交付
```

本地测试：

```env
MOCK_AUTH=true
VITE_ENABLE_MOCK_AUTH=true
```

本地假凭证：

```text
http://localhost:23001/?ticket=test
```

## 12. 联调用例

| 场景 | 输入 | 预期 |
| --- | --- | --- |
| 有效 ticket | `https://yunheai.cloud/?ticket=有效凭证` | 正常进入，显示当前用户，URL 中 ticket 被清理 |
| 无 ticket | `https://yunheai.cloud/` | 无登录态时被拦截 |
| 无效 ticket | `?ticket=无效凭证` | 返回 `CREDENTIAL_INVALID` |
| 过期 ticket | `?ticket=过期凭证` | 返回 `CREDENTIAL_EXPIRED` |
| 已使用 ticket | 重复使用一次性凭证 | 返回 `CREDENTIAL_USED` |
| 禁用用户 | ticket 对应禁用账号 | 返回 `USER_DISABLED` |
| 校验接口超时 | 采购中国接口超时 | 返回 `VERIFY_TIMEOUT` 或 `VERIFY_FAILED` |
| 未登录调用 API | 无 Bearer token 调 `/chat/run` | 返回 401/403 |

## 13. 上线检查清单

```text
[ ] https://yunheai.cloud/fLWSO3QWD6.txt 可访问
[ ] 采购中国小程序后台已配置 yunheai.cloud 为 web-view 业务域名
[ ] 采购中国小程序可打开 https://yunheai.cloud/?ticket={ticket}
[ ] MOCK_AUTH=false
[ ] VITE_ENABLE_MOCK_AUTH=false
[ ] INSTANCE_JWT_SECRET 已替换为强密钥
[ ] CAIGOU_CHINA_AUTH_VERIFY_URL 已配置真实地址
[ ] CAIGOU_CHINA_APP_SECRET 已通过安全渠道配置
[ ] 有效 ticket 可登录
[ ] 登录成功后 URL 中 ticket 被清理
[ ] 页面展示当前用户名称/昵称
[ ] 无 ticket 且无登录态时被拦截
[ ] 无效/过期/已使用 ticket 被拦截并展示产品提示
[ ] 后端 API 未登录返回 401/403
[ ] 日志不记录完整 ticket、appSecret 或手机号明文
```
