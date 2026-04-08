# Vector Database Benchmark - 向量数据库对比测试

**测试编号**: BM-VDB-2026-02-11
**测试版本**: v1.0 (大纲)
**状态**: 📅 计划中

---

## 候选数据库

| 数据库 | 特点 | GitHub Stars | 许可证 |
|--------|------|-------------|--------|
| **Qdrant** | Rust 编写，性能优秀 | 18K+ | Apache 2.0 |
| **Weaviate** | GraphQL API，功能丰富 | 9K+ | BSD-3 |
| **Milvus** | 分布式，企业级 | 27K+ | Apache 2.0 |
| **ChromaDB** | Python 原生，轻量级 | 12K+ | Apache 2.0 |
| **Pinecone** | 托管服务，免费额度 | N/A (SaaS) | 商业 |

## 测试维度

1. **性能测试**
   - 插入速度 (vectors/sec)
   - 查询延迟 (P50, P95, P99)
   - 并发能力

2. **准确率测试**
   - Recall@10
   - 不同索引算法对比 (HNSW, IVF, etc.)

3. **成本测试**
   - 存储成本
   - 查询成本
   - 资源消耗（内存、CPU）

4. **易用性**
   - API 友好度
   - 文档质量
   - 部署难度

## 推荐

**Phase 0**: Qdrant（本地部署，性能优秀）
**Phase 1**: Pinecone（托管服务，运维简单）

---

**参考资料**:
- Qdrant - https://qdrant.tech/
- Weaviate - https://weaviate.io/
- Milvus - https://milvus.io/
- ANN Benchmarks - https://ann-benchmarks.com/
