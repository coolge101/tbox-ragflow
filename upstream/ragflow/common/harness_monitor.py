#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import json
import time
import threading
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import logging

from .log_utils import init_root_logger

# 初始化日志
init_root_logger("harness_monitor")

logger = logging.getLogger(__name__)


class SecurityEventType(str, Enum):
    """安全事件类型"""
    PROMPT_INJECTION = "prompt_injection"
    CONTENT_VIOLATION = "content_violation"
    RESOURCE_ABUSE = "resource_abuse"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SYSTEM_ERROR = "system_error"
    PERFORMANCE_DEGRADATION = "performance_degradation"


class DecisionOutcome(str, Enum):
    """决策结果"""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    MODIFIED = "modified"
    ESCALATED = "escalated"


@dataclass
class DecisionTrace:
    """决策追踪记录"""
    decision_id: str
    timestamp: datetime
    component: str
    input_data: Dict[str, Any]
    reasoning_chain: List[Dict[str, Any]]
    constraints_applied: List[str]
    outcome: DecisionOutcome
    confidence_score: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self):
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class SecurityEvent:
    """安全事件记录"""
    event_id: str
    timestamp: datetime
    event_type: SecurityEventType
    severity: str  # low, medium, high, critical
    component: str
    description: str
    details: Dict[str, Any]
    action_taken: str
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def to_dict(self):
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolution_time:
            data['resolution_time'] = self.resolution_time.isoformat()
        return data


@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime
    component: str
    response_time_ms: float
    throughput_rps: float
    error_rate: float
    resource_usage: Dict[str, float]  # cpu, memory, etc.
    custom_metrics: Dict[str, Any] = None
    
    def to_dict(self):
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class HarnessMonitor:
    """Harness Engineering 监控代理"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.decision_traces: List[DecisionTrace] = []
        self.security_events: List[SecurityEvent] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        
        # 线程安全锁
        self._lock = threading.RLock()
        
        # 事件处理器
        self._event_handlers: Dict[SecurityEventType, List[Callable]] = {}
        
        # 初始化配置
        self._init_config()
        
        logger.info("HarnessMonitor initialized")
    
    def _init_config(self):
        """初始化配置"""
        self.max_traces = self.config.get('max_traces', 10000)
        self.max_events = self.config.get('max_events', 10000)
        self.max_metrics = self.config.get('max_metrics', 10000)
        
        # 告警阈值
        self.alert_thresholds = self.config.get('alert_thresholds', {
            'response_time_ms': 5000,
            'error_rate': 0.05,
            'memory_usage_percent': 80
        })
    
    def track_decision(self, component: str, input_data: Dict[str, Any], 
                      reasoning_chain: List[Dict[str, Any]], 
                      constraints_applied: List[str],
                      outcome: DecisionOutcome,
                      confidence_score: float = 1.0,
                      metadata: Dict[str, Any] = None) -> str:
        """
        追踪AI决策过程
        
        Args:
            component: 组件名称
            input_data: 输入数据
            reasoning_chain: 推理链
            constraints_applied: 应用的约束
            outcome: 决策结果
            confidence_score: 置信度评分 (0.0-1.0)
            metadata: 额外元数据
            
        Returns:
            决策ID
        """
        decision_id = f"decision_{int(time.time() * 1000)}_{len(self.decision_traces)}"
        
        trace = DecisionTrace(
            decision_id=decision_id,
            timestamp=datetime.now(),
            component=component,
            input_data=input_data,
            reasoning_chain=reasoning_chain,
            constraints_applied=constraints_applied,
            outcome=outcome,
            confidence_score=confidence_score,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.decision_traces.append(trace)
            # 限制存储数量
            if len(self.decision_traces) > self.max_traces:
                self.decision_traces = self.decision_traces[-self.max_traces:]
        
        logger.debug(f"Decision tracked: {decision_id}, outcome: {outcome}")
        return decision_id
    
    def record_security_event(self, event_type: SecurityEventType, 
                             severity: str, component: str, 
                             description: str, details: Dict[str, Any],
                             action_taken: str) -> str:
        """
        记录安全事件
        
        Args:
            event_type: 事件类型
            severity: 严重程度
            component: 组件名称
            description: 事件描述
            details: 事件详情
            action_taken: 采取的行动
            
        Returns:
            事件ID
        """
        event_id = f"event_{int(time.time() * 1000)}_{len(self.security_events)}"
        
        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            component=component,
            description=description,
            details=details,
            action_taken=action_taken
        )
        
        with self._lock:
            self.security_events.append(event)
            # 限制存储数量
            if len(self.security_events) > self.max_events:
                self.security_events = self.security_events[-self.max_events:]
        
        # 触发事件处理器
        self._trigger_event_handlers(event)
        
        logger.warning(f"Security event recorded: {event_id}, type: {event_type}, severity: {severity}")
        return event_id
    
    def record_metrics(self, component: str, response_time_ms: float,
                      throughput_rps: float, error_rate: float,
                      resource_usage: Dict[str, float],
                      custom_metrics: Dict[str, Any] = None) -> str:
        """
        记录性能指标
        
        Args:
            component: 组件名称
            response_time_ms: 响应时间(毫秒)
            throughput_rps: 吞吐量(请求/秒)
            error_rate: 错误率
            resource_usage: 资源使用情况
            custom_metrics: 自定义指标
            
        Returns:
            指标ID
        """
        metric_id = f"metric_{int(time.time() * 1000)}_{len(self.performance_metrics)}"
        
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            component=component,
            response_time_ms=response_time_ms,
            throughput_rps=throughput_rps,
            error_rate=error_rate,
            resource_usage=resource_usage,
            custom_metrics=custom_metrics or {}
        )
        
        with self._lock:
            self.performance_metrics.append(metrics)
            # 限制存储数量
            if len(self.performance_metrics) > self.max_metrics:
                self.performance_metrics = self.performance_metrics[-self.max_metrics:]
        
        # 检查告警阈值
        self._check_alert_thresholds(metrics)
        
        logger.debug(f"Metrics recorded: {metric_id}, component: {component}")
        return metric_id
    
    def _check_alert_thresholds(self, metrics: PerformanceMetrics):
        """检查性能指标是否超过告警阈值"""
        alerts = []
        
        if metrics.response_time_ms > self.alert_thresholds.get('response_time_ms', 5000):
            alerts.append(f"High response time: {metrics.response_time_ms}ms")
        
        if metrics.error_rate > self.alert_thresholds.get('error_rate', 0.05):
            alerts.append(f"High error rate: {metrics.error_rate}")
        
        memory_usage = metrics.resource_usage.get('memory_percent', 0)
        if memory_usage > self.alert_thresholds.get('memory_usage_percent', 80):
            alerts.append(f"High memory usage: {memory_usage}%")
        
        if alerts:
            self.record_security_event(
                event_type=SecurityEventType.PERFORMANCE_DEGRADATION,
                severity="medium",
                component=metrics.component,
                description="Performance degradation detected",
                details={
                    "alerts": alerts,
                    "metrics": metrics.to_dict()
                },
                action_taken="alert_raised"
            )
    
    def _trigger_event_handlers(self, event: SecurityEvent):
        """触发事件处理器"""
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    def register_event_handler(self, event_type: SecurityEventType, handler: Callable):
        """注册事件处理器"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def get_decision_trace(self, decision_id: str) -> Optional[DecisionTrace]:
        """获取决策追踪记录"""
        with self._lock:
            for trace in self.decision_traces:
                if trace.decision_id == decision_id:
                    return trace
        return None
    
    def get_recent_decisions(self, limit: int = 100) -> List[DecisionTrace]:
        """获取最近的决策记录"""
        with self._lock:
            return self.decision_traces[-limit:] if self.decision_traces else []
    
    def get_security_events(self, event_type: Optional[SecurityEventType] = None,
                           severity: Optional[str] = None,
                           resolved: Optional[bool] = None,
                           limit: int = 100) -> List[SecurityEvent]:
        """获取安全事件"""
        with self._lock:
            events = self.security_events
            
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            if severity:
                events = [e for e in events if e.severity == severity]
            if resolved is not None:
                events = [e for e in events if e.resolved == resolved]
            
            return events[-limit:] if events else []
    
    def get_performance_metrics(self, component: Optional[str] = None,
                               time_range_minutes: Optional[int] = None,
                               limit: int = 100) -> List[PerformanceMetrics]:
        """获取性能指标"""
        with self._lock:
            metrics = self.performance_metrics
            
            if component:
                metrics = [m for m in metrics if m.component == component]
            
            if time_range_minutes:
                cutoff_time = datetime.now().timestamp() - (time_range_minutes * 60)
                metrics = [m for m in metrics if m.timestamp.timestamp() > cutoff_time]
            
            return metrics[-limit:] if metrics else []
    
    def resolve_security_event(self, event_id: str, resolution_notes: str = ""):
        """解决安全事件"""
        with self._lock:
            for event in self.security_events:
                if event.event_id == event_id and not event.resolved:
                    event.resolved = True
                    event.resolution_time = datetime.now()
                    if resolution_notes:
                        event.details['resolution_notes'] = resolution_notes
                    logger.info(f"Security event resolved: {event_id}")
                    return True
        return False
    
    def generate_report(self, report_type: str = "summary", 
                       time_range_minutes: int = 60) -> Dict[str, Any]:
        """生成监控报告"""
        cutoff_time = datetime.now().timestamp() - (time_range_minutes * 60)
        
        with self._lock:
            # 筛选时间范围内的数据
            recent_decisions = [
                d for d in self.decision_traces 
                if d.timestamp.timestamp() > cutoff_time
            ]
            recent_events = [
                e for e in self.security_events
                if e.timestamp.timestamp() > cutoff_time
            ]
            recent_metrics = [
                m for m in self.performance_metrics
                if m.timestamp.timestamp() > cutoff_time
            ]
        
        # 计算统计信息
        decision_stats = {
            "total": len(recent_decisions),
            "by_outcome": {},
            "avg_confidence": 0
        }
        
        if recent_decisions:
            outcome_counts = {}
            total_confidence = 0
            for decision in recent_decisions:
                outcome_counts[decision.outcome] = outcome_counts.get(decision.outcome, 0) + 1
                total_confidence += decision.confidence_score
            
            decision_stats["by_outcome"] = outcome_counts
            decision_stats["avg_confidence"] = total_confidence / len(recent_decisions)
        
        # 安全事件统计
        event_stats = {
            "total": len(recent_events),
            "by_type": {},
            "by_severity": {},
            "resolved": len([e for e in recent_events if e.resolved]),
            "unresolved": len([e for e in recent_events if not e.resolved])
        }
        
        for event in recent_events:
            event_stats["by_type"][event.event_type] = event_stats["by_type"].get(event.event_type, 0) + 1
            event_stats["by_severity"][event.severity] = event_stats["by_severity"].get(event.severity, 0) + 1
        
        # 性能指标统计
        metric_stats = {}
        if recent_metrics:
            avg_response_time = sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics)
            avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
            
            metric_stats = {
                "avg_response_time_ms": avg_response_time,
                "avg_error_rate": avg_error_rate,
                "total_metrics": len(recent_metrics)
            }
        
        report = {
            "report_type": report_type,
            "time_range_minutes": time_range_minutes,
            "generated_at": datetime.now().isoformat(),
            "decision_stats": decision_stats,
            "event_stats": event_stats,
            "metric_stats": metric_stats,
            "summary": {
                "system_health": self._calculate_system_health(event_stats, metric_stats),
                "recommendations": self._generate_recommendations(event_stats, metric_stats)
            }
        }
        
        return report
    
    def _calculate_system_health(self, event_stats: Dict, metric_stats: Dict) -> str:
        """计算系统健康状态"""
        # 基于安全事件和性能指标计算健康状态
        unresolved_critical = event_stats.get("by_severity", {}).get("critical", 0)
        unresolved_high = event_stats.get("by_severity", {}).get("high", 0)
        
        avg_error_rate = metric_stats.get("avg_error_rate", 0)
        avg_response_time = metric_stats.get("avg_response_time_ms", 0)
        
        if unresolved_critical > 0 or avg_error_rate > 0.1:
            return "critical"
        elif unresolved_high > 0 or avg_error_rate > 0.05 or avg_response_time > 10000:
            return "warning"
        else:
            return "healthy"
    
    def _generate_recommendations(self, event_stats: Dict, metric_stats: Dict) -> List[str]:
        """生成推荐建议"""
        recommendations = []
        
        # 基于安全事件的建议
        unresolved = event_stats.get("unresolved", 0)
        if unresolved > 0:
            recommendations.append(f"有 {unresolved} 个未解决的安全事件需要处理")
        
        critical_events = event_stats.get("by_severity", {}).get("critical", 0)
        if critical_events > 0:
            recommendations.append(f"有 {critical_events} 个严重安全事件需要立即处理")
        
        # 基于性能指标的建议
        avg_error_rate = metric_stats.get("avg_error_rate", 0)
        if avg_error_rate > 0.05:
            recommendations.append(f"错误率较高 ({avg_error_rate:.2%})，建议检查系统稳定性")
        
        avg_response_time = metric_stats.get("avg_response_time_ms", 0)
        if avg_response_time > 5000:
            recommendations.append(f"响应时间较慢 ({avg_response_time:.0f}ms)，建议优化性能")
        
        if not recommendations:
            recommendations.append("系统运行正常，无需立即操作")
        
        return recommendations
    
    def export_data(self, data_type: str = "all", format: str = "json") -> str:
        """导出监控数据"""
        with self._lock:
            if data_type == "decisions":
                data = [trace.to_dict() for trace in self.decision_traces]
            elif data_type == "events":
                data = [event.to_dict() for event in self.security_events]
            elif data_type == "metrics":
                data = [metric.to_dict() for metric in self.performance_metrics]
            else:  # all
                data = {
                    "decisions": [trace.to_dict() for trace in self.decision_traces],
                    "events": [event.to_dict() for event in self.security_events],
                    "metrics": [metric.to_dict() for metric in self.performance_metrics]
                }
        
        if format == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format}")


# 全局监控实例
_global_monitor: Optional[HarnessMonitor] = None


def get_global_monitor(config: Dict[str, Any] = None) -> HarnessMonitor:
    """获取全局监控实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = HarnessMonitor(config)
    return _global_monitor


def track_decision(*args, **kwargs) -> str:
    """追踪决策（便捷函数）"""
    monitor = get_global_monitor()
    return monitor.track_decision(*args, **kwargs)


def record_security_event(*args, **kwargs) -> str:
    """记录安全事件（便捷函数）"""
    monitor = get_global_monitor()
    return monitor.record_security_event(*args, **kwargs)


def record_metrics(*args, **kwargs) -> str:
    """记录性能指标（便捷函数）"""
    monitor = get_global_monitor()
    return monitor.record_metrics(*args, **kwargs)