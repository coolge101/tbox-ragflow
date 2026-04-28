# RAGFlow Harness Engineering 使用指南

## 概述

Harness Engineering（约束/控制工程）为RAGFlow AI系统建立了安全边界和控制机制，确保系统在预设范围内安全、可靠地运行。本指南介绍如何开始使用我们建立的Harness Engineering系统。

## 已完成的组件

### 1. AI安全约束框架 (`common/harness_monitor.py`)

**功能**：
- AI决策追踪和审计
- 安全事件监控和记录
- 性能指标收集和分析
- 可解释性报告生成

**核心类**：
- `HarnessMonitor`: 主监控类
- `SecurityEventType`: 安全事件类型枚举
- `DecisionOutcome`: 决策结果枚举
- `DecisionTrace`: 决策追踪记录
- `SecurityEvent`: 安全事件记录
- `PerformanceMetrics`: 性能指标

**使用方法**：

```python
from common.harness_monitor import (
    HarnessMonitor, get_global_monitor,
    SecurityEventType, DecisionOutcome,
    track_decision, record_security_event, record_metrics
)

# 使用全局监控器
monitor = get_global_monitor()

# 追踪AI决策
decision_id = monitor.track_decision(
    component="llm_service",
    input_data={"query": "用户查询"},
    reasoning_chain=[{"step": "分析", "result": "安全"}],
    constraints_applied=["无有害内容"],
    outcome=DecisionOutcome.ALLOWED,
    confidence_score=0.95
)

# 记录安全事件
event_id = monitor.record_security_event(
    event_type=SecurityEventType.PROMPT_INJECTION,
    severity="high",
    component="api_gateway",
    description="检测到提示注入尝试",
    details={"payload": "忽略之前指令"},
    action_taken="请求被阻止"
)

# 记录性能指标
metric_id = monitor.record_metrics(
    component="llm_service",
    response_time_ms=150.5,
    throughput_rps=10.2,
    error_rate=0.01,
    resource_usage={"cpu_percent": 45.5, "memory_percent": 60.2}
)

# 生成报告
report = monitor.generate_report(time_range_minutes=60)
```

### 2. 对抗性测试框架 (`test/adversarial_tests.py`)

**功能**：
- 预定义攻击向量库（提示注入、SQL注入、XSS等）
- 模糊测试生成
- 安全评分计算
- 详细测试报告

**使用方法**：

```bash
# 运行对抗性测试
python test/adversarial_tests.py --target http://localhost:9380 --fuzz-count 50 --output security_report.json

# 只运行特定测试类型
python -m pytest test/adversarial_tests.py::test_prompt_injection_defense -v

# 集成到pytest
pytest test/adversarial_tests.py -m adversarial
```

**攻击类型**：
- `PROMPT_INJECTION`: 提示注入攻击
- `SQL_INJECTION`: SQL注入攻击  
- `JAVASCRIPT_INJECTION`: JavaScript/XSS攻击
- `COMMAND_INJECTION`: 命令注入攻击
- `PATH_TRAVERSAL`: 路径遍历攻击
- `DOS`: 拒绝服务攻击
- `DATA_LEAKAGE`: 数据泄露攻击

### 3. CI/CD集成 (`.github/workflows/harness_engineering.yml`)

**触发条件**：
- 推送代码到main分支
- Pull Request创建/更新
- 每天凌晨2点自动运行
- 手动触发

**测试阶段**：
1. **静态安全分析**：Bandit + Safety
2. **单元测试**：Harness Monitor组件测试
3. **对抗性测试**：运行预定义攻击向量
4. **安全集成测试**：API安全头、输入验证等
5. **报告生成**：综合安全评分和建议

## 快速开始

### 步骤1：安装依赖

```bash
cd /home/vboxuser/ragflow
uv sync --python 3.12 --group test --frozen
source .venv/bin/activate
uv pip install requests pytest bandit safety
```

### 步骤2：运行基本测试

```bash
# 运行Harness Monitor单元测试
pytest test/test_harness_monitor.py -v

# 运行静态安全分析
bandit -r common/ -f json -o bandit_report.json
safety check --json > safety_report.json

# 验证对抗性测试框架
python test/adversarial_tests.py --dry-run
```

### 步骤3：集成到应用代码

在您的RAGFlow应用中集成Harness Monitor：

```python
# 在API端点中添加监控
from fastapi import FastAPI, Request
from common.harness_monitor import track_decision, record_security_event

app = FastAPI()

@app.post("/v1/chat/completions")
async def chat_completion(request: Request):
    data = await request.json()
    
    # 监控决策过程
    decision_id = track_decision(
        component="chat_api",
        input_data=data,
        reasoning_chain=[{"step": "input_validation", "result": "valid"}],
        constraints_applied=["content_filter", "rate_limit"],
        outcome="allowed",
        confidence_score=0.9
    )
    
    # 处理请求...
    
    return response
```

### 步骤4：运行完整安全测试

```bash
# 启动RAGFlow服务
cd docker
docker-compose up -d

# 等待服务启动
sleep 30

# 运行对抗性测试
cd ..
python test/adversarial_tests.py --target http://localhost:9380 --fuzz-count 20

# 查看报告
cat adversarial_test_report.json | jq '.summary'
```

## 测试策略

### 1. 开发阶段测试
- 每次提交运行单元测试
- 代码审查时运行静态分析
- 本地开发环境运行快速对抗性测试

### 2. CI/CD流水线测试
- PR合并前运行完整安全测试
- 每日定时运行深度安全扫描
- 发布前运行渗透测试

### 3. 生产环境监控
- 实时监控安全事件
- 定期生成安全报告
- 异常行为自动告警

## 安全指标

### 技术指标
- **安全评分**: 0-100分，基于测试通过率
- **漏洞数量**: 发现的严重/高危漏洞
- **响应时间**: 安全检查对性能的影响
- **覆盖率**: 安全测试代码覆盖率

### 业务指标
- **安全事件响应时间**: <15分钟
- **漏洞修复时间**: 严重漏洞<24小时
- **合规性**: 安全审计通过率
- **用户信任度**: 安全功能使用率

## 最佳实践

### 1. 监控集成
- 在所有关键决策点添加监控
- 记录完整的推理链
- 设置合理的告警阈值

### 2. 测试策略
- 定期更新攻击向量库
- 结合手动和自动测试
- 模拟真实攻击场景

### 3. 响应机制
- 建立安全事件响应流程
- 定期演练应急响应
- 持续改进安全策略

## 故障排除

### 常见问题

1. **导入错误**: 确保`common/harness_monitor.py`在Python路径中
2. **测试失败**: 检查RAGFlow服务是否正常运行
3. **性能问题**: 调整监控采样率，避免过度监控
4. **报告生成失败**: 检查文件权限和磁盘空间

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查监控数据
monitor = get_global_monitor()
print(f"决策记录数: {len(monitor.decision_traces)}")
print(f"安全事件数: {len(monitor.security_events)}")

# 导出数据进行分析
json_data = monitor.export_data(data_type="all", format="json")
with open("monitor_data.json", "w") as f:
    f.write(json_data)
```

## 下一步

### 短期目标（1-2周）
1. 将Harness Monitor集成到核心业务逻辑
2. 建立安全事件告警机制
3. 培训开发团队使用安全工具

### 中期目标（1-2月）
1. 实现自动化红队测试
2. 建立安全仪表板
3. 集成第三方安全工具

### 长期目标（3-6月）
1. 获得安全认证（如ISO 27001）
2. 建立完整的安全运营中心
3. 开源安全组件和最佳实践

## 支持与反馈

- **文档**: 查看`harness_engineering_strategy.md`获取详细设计
- **问题**: 在GitHub Issues报告安全问题
- **贡献**: 欢迎提交新的攻击向量和测试用例
- **联系**: 安全团队邮箱 security@ragflow.io

---

**安全第一，持续改进**