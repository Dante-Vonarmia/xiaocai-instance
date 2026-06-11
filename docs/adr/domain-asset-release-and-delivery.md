# Domain Asset Release and Delivery

## Status

Draft / Proposal

## Date

2026-06-11

## Context

`domain-packs/xiaocai/` 当前既是采购领域资产源，又被前端、API、kernel 和部署脚本作为运行时资源读取。一次线上问题暴露出交付链路缺口：本地测试环境通过 compose volume 挂载 `domain-packs`，而线上 standalone 前端只部署了 `dist`，导致 `/domain-packs/xiaocai/app-profile.json` 回退成 `index.html`，前端未拿到 `capabilityCatalog` 与 `composerModeOptions`。

这说明 `domain-packs` 已经不是附属静态文件，而是产品运行时契约的一部分。它需要进入标准化的上传、构建、部署、校验、回滚和管理流程。

## Decision

建立 `Domain Asset Release` 机制：本地、测试、线上不再各自“碰运气”读取散落文件，而是统一消费同一份已构建、已校验、可回滚的 domain asset snapshot。

职责边界如下：

1. FLARE 负责通用机制：
   - asset schema / validator
   - loader contract
   - capability / mode canonical contract
   - runtime snapshot 读取协议
   - failure / fallback protocol
2. xiaocai 负责采购业务资产：
   - fields / taxonomy / workflow
   - templates / prompts
   - capability catalog
   - composer modes
   - app profile / branding projection
3. delivery pipeline 负责把 xiaocai 业务资产发布成不可变 snapshot，并保证所有环境消费同一份 snapshot。

## Non-Goals

1. 不在 xiaocai 本地实现 FLARE runtime、mode、intent、capability dispatch 或 workflow kernel。
2. 不把采购业务字段、模板、按钮文案、寻源策略写入 FLARE core。
3. 不把线上手动改文件作为常规交付方式。
4. 不把 UI projection 当成 authoritative state。

## Proposed Runtime Shape

目标运行时消费形态：

```text
domain source assets
  -> validate
  -> build domain asset snapshot
  -> publish with frontend/backend release
  -> runtime reads snapshot
  -> post-deploy smoke verifies asset contract
```

snapshot 最小内容：

```text
domain-assets/xiaocai/
  release.json
  app-profile.json
  fields.json
  workflow.json
  templates/
  checksums.json
```

`release.json` 至少记录：

```json
{
  "domain": "xiaocai",
  "git_sha": "...",
  "built_at": "2026-06-11T14:35:00Z",
  "asset_hash": "...",
  "capabilities": ["requirement_intake", "analysis_mode", "sourcing"]
}
```

## Delivery Requirements

发布流程必须标准化以下动作：

1. 构建前校验
   - domain asset schema 校验
   - capability key 与 workflow/mode contract 对齐
   - app-profile 必须包含 `capabilityCatalog` 与 `composerModeOptions`
2. 构建
   - 生成 domain asset snapshot
   - 生成 checksums
   - 记录 git sha 与构建时间
3. 部署
   - frontend dist 与 domain asset snapshot 一起部署
   - backend/kernel 使用同一份资产源或同一 snapshot
   - `/domain-packs/*` 或未来 `/domain-assets/*` 禁止 fallback 到 `index.html`
4. 发布后 smoke
   - `app-profile.json` 可访问
   - `Content-Type` 为 JSON
   - `capabilityCatalog` 非空
   - `composerModeOptions` 非空
   - 线上 asset hash 与构建产物一致
5. 回滚
   - 能按 release id / git sha 回滚 domain asset snapshot
   - 回滚不依赖手动编辑线上文件

## Configuration Ownership

配置分为两类：

1. 稳定协议类，文件化并走代码审查：
   - field schema contract
   - workflow contract
   - template contract
   - capability registry contract
2. 运营配置类，后续可进入数据库或配置中心：
   - starter prompts
   - 能力展示开关
   - 默认模式
   - 品牌文案
   - 客户级 override

无论配置存储在文件、数据库还是对象存储，运行时都应消费发布后的 snapshot，而不是直接消费散乱源配置。

## CI/CD Gates

最小 CI/CD gate：

1. `validate-domain-assets`
2. `build-domain-asset-snapshot`
3. `compare-snapshot-checksums`
4. `frontend-static-route-smoke`
5. `api-domain-asset-smoke`
6. `post-deploy-domain-asset-smoke`

任何 gate 失败，都不应标记发布完成。

## Weekend Implementation Plan

### Step 1: Stop the bleeding

- 将 `domain-packs` 纳入 standalone 前端发布脚本。
- nginx/openresty 对 `/domain-packs/*` 使用 `try_files $uri =404`。
- 发布后强制 curl + JSON parse。

### Step 2: Build the release contract

- 新增 domain asset release manifest。
- 新增 checksum 生成与校验脚本。
- 统一本地、测试、线上 asset hash 输出。

### Step 3: Add CI/CD acceptance

- 在 CI 中跑 domain asset validator。
- 在部署脚本中跑 post-deploy smoke。
- 发布日志必须记录 asset hash、git sha、目标环境和回滚点。

### Step 4: Prepare future config center

- 明确哪些配置仍留在 repo。
- 明确哪些配置迁移到 config center / database。
- 保持 runtime snapshot 作为唯一消费面。

## Acceptance Criteria

1. 本地、测试、线上读取到的 app-profile hash 一致。
2. 线上 `/domain-packs/xiaocai/app-profile.json` 不再返回 HTML。
3. 能力按钮来自发布后的 `capabilityCatalog`，不是前端 fallback。
4. 新发布流程不需要手动登录服务器复制 domain assets。
5. 发布失败时能明确知道失败在 build、deploy、route、asset parse 还是 contract mismatch。
6. rollback 能恢复上一份 domain asset snapshot。

## Open Questions

1. snapshot 目录命名使用 `domain-assets/` 还是兼容保留 `domain-packs/`。
2. asset release manifest 由 xiaocai repo 生成，还是后续交给 FLARE 通用工具生成。
3. config center 首批承接哪些运营配置。
4. 是否需要为每个客户/tenant 引入独立 override snapshot。
5. 是否将前端读取从静态路径迁移到 xiaocai API，例如 `/api/v1/domain-assets/xiaocai/app-profile`。

## Current Safety Note

2026-06-11 的线上修复属于止血热修：同步缺失的 `domain-packs` 并修正 openresty 静态路由。该动作必须回收进正式发布流程，不能作为长期交付方式。
