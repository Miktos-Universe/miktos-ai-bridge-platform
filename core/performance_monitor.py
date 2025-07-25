"""
Real-time Performance Monitor for Miktos AI Platform
Priority 3: Real-time Features & Optimization

Provides comprehensive performance monitoring, bottleneck detection,
and automated optimization for sub-1-minute workflow execution.
"""

import asyncio
import logging
import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque, defaultdict
import json
import weakref

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric data point"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    context: Dict[str, Any]
    source: str


@dataclass
class PerformanceTarget:
    """Performance target configuration"""
    name: str
    current_value: float
    target_value: float
    unit: str
    status: str  # "meeting", "approaching", "failing"
    trend: str   # "improving", "stable", "degrading"


@dataclass
class BottleneckAlert:
    """Performance bottleneck alert"""
    timestamp: datetime
    component: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    suggested_action: str
    metrics: Dict[str, float]


class PerformanceCollector:
    """Collects various performance metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.command_timings = deque(maxlen=100)
        self.workflow_timings = deque(maxlen=50)
        self.cache_stats = defaultdict(float)
        self.websocket_stats = defaultdict(int)
        
    async def collect_system_metrics(self) -> Dict[str, float]:
        """Collect system-level performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network stats (if available)
            network = psutil.net_io_counters()
            
            return {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_usage_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                'network_bytes_sent': network.bytes_sent if network else 0,
                'network_bytes_recv': network.bytes_recv if network else 0,
            }
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}
    
    def record_command_timing(self, command: str, duration: float, success: bool):
        """Record command execution timing"""
        self.command_timings.append({
            'timestamp': datetime.now(),
            'command': command,
            'duration': duration,
            'success': success
        })
    
    def record_workflow_timing(self, workflow_id: str, duration: float, steps: int):
        """Record workflow execution timing"""
        self.workflow_timings.append({
            'timestamp': datetime.now(),
            'workflow_id': workflow_id,
            'duration': duration,
            'steps': steps,
            'avg_step_time': duration / max(steps, 1)
        })
    
    def record_cache_operation(self, operation: str, hit: bool, duration: float):
        """Record cache operation statistics"""
        self.cache_stats[f'{operation}_total'] += 1
        if hit:
            self.cache_stats[f'{operation}_hits'] += 1
        self.cache_stats[f'{operation}_total_time'] += duration
    
    def record_websocket_activity(self, event_type: str, user_count: int):
        """Record WebSocket activity for collaboration metrics"""
        self.websocket_stats[f'{event_type}_count'] += 1
        self.websocket_stats['active_users'] = user_count
    
    def get_avg_command_time(self, last_n: int = 10) -> float:
        """Get average command execution time"""
        if not self.command_timings:
            return 0.0
        
        recent_timings = list(self.command_timings)[-last_n:]
        if not recent_timings:
            return 0.0
        
        return sum(t['duration'] for t in recent_timings) / len(recent_timings)
    
    def get_cache_hit_rate(self, operation: str = 'get') -> float:
        """Get cache hit rate for specified operation"""
        total_key = f'{operation}_total'
        hits_key = f'{operation}_hits'
        
        total = self.cache_stats.get(total_key, 0)
        hits = self.cache_stats.get(hits_key, 0)
        
        return hits / max(total, 1)


class PerformanceAnalyzer:
    """Analyzes performance metrics and detects bottlenecks"""
    
    def __init__(self, targets: Dict[str, float]):
        self.targets = targets
        self.metric_history = defaultdict(lambda: deque(maxlen=100))
        self.alerts = []
    
    def add_metric(self, metric: PerformanceMetric):
        """Add a metric data point for analysis"""
        self.metric_history[metric.metric_name].append(metric)
    
    def analyze_trends(self, metric_name: str, window_size: int = 10) -> str:
        """Analyze performance trends for a metric"""
        history = list(self.metric_history[metric_name])
        if len(history) < window_size:
            return "insufficient_data"
        
        recent_values = [m.value for m in history[-window_size:]]
        older_values = [m.value for m in history[-window_size*2:-window_size]]
        
        if not older_values:
            return "stable"
        
        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)
        
        if recent_avg > older_avg * 1.1:
            return "degrading"
        elif recent_avg < older_avg * 0.9:
            return "improving"
        else:
            return "stable"
    
    def check_targets(self, current_metrics: Dict[str, float]) -> List[PerformanceTarget]:
        """Check current metrics against performance targets"""
        targets = []
        
        for target_name, target_value in self.targets.items():
            current_value = current_metrics.get(target_name, 0)
            
            # Determine status
            if target_name.startswith('max_'):
                # For maximum targets (smaller is better)
                if current_value <= target_value:
                    status = "meeting"
                elif current_value <= target_value * 1.2:
                    status = "approaching"
                else:
                    status = "failing"
            else:
                # For minimum targets (larger is better)
                if current_value >= target_value:
                    status = "meeting"
                elif current_value >= target_value * 0.8:
                    status = "approaching"
                else:
                    status = "failing"
            
            # Determine trend
            trend = self.analyze_trends(target_name)
            
            targets.append(PerformanceTarget(
                name=target_name,
                current_value=current_value,
                target_value=target_value,
                unit=self._get_unit(target_name),
                status=status,
                trend=trend
            ))
        
        return targets
    
    def detect_bottlenecks(self, metrics: Dict[str, float]) -> List[BottleneckAlert]:
        """Detect performance bottlenecks and generate alerts"""
        alerts = []
        current_time = datetime.now()
        
        # CPU bottleneck
        if metrics.get('cpu_usage_percent', 0) > 90:
            alerts.append(BottleneckAlert(
                timestamp=current_time,
                component="CPU",
                severity="high",
                description="CPU usage is critically high",
                suggested_action="Consider reducing parallel operations or upgrading hardware",
                metrics={'cpu_usage': metrics.get('cpu_usage_percent', 0)}
            ))
        
        # Memory bottleneck
        if metrics.get('memory_usage_percent', 0) > 85:
            alerts.append(BottleneckAlert(
                timestamp=current_time,
                component="Memory",
                severity="high",
                description="Memory usage is approaching limits",
                suggested_action="Clear caches, reduce concurrent operations, or increase memory",
                metrics={'memory_usage': metrics.get('memory_usage_percent', 0)}
            ))
        
        # Workflow performance
        avg_workflow_time = metrics.get('avg_workflow_time', 0)
        if avg_workflow_time > 60:  # Sub-1-minute target
            alerts.append(BottleneckAlert(
                timestamp=current_time,
                component="Workflows",
                severity="medium",
                description=f"Average workflow time ({avg_workflow_time:.1f}s) exceeds 1-minute target",
                suggested_action="Enable more aggressive caching or optimize workflow steps",
                metrics={'avg_workflow_time': avg_workflow_time}
            ))
        
        # Cache performance
        cache_hit_rate = metrics.get('cache_hit_rate', 0)
        if cache_hit_rate < 0.8:  # 80% target
            alerts.append(BottleneckAlert(
                timestamp=current_time,
                component="Cache",
                severity="medium",
                description=f"Cache hit rate ({cache_hit_rate:.1%}) below 80% target",
                suggested_action="Improve cache warming or adjust cache TTL settings",
                metrics={'cache_hit_rate': cache_hit_rate}
            ))
        
        return alerts
    
    def _get_unit(self, metric_name: str) -> str:
        """Get appropriate unit for metric"""
        if 'time' in metric_name.lower():
            return "seconds"
        elif 'rate' in metric_name.lower():
            return "percentage"
        elif 'fps' in metric_name.lower():
            return "frames/sec"
        else:
            return "units"


class OptimizationEngine:
    """Automated performance optimization engine"""
    
    def __init__(self, performance_monitor):
        self.monitor = performance_monitor
        self.optimization_history = []
        self.auto_optimize = True
    
    async def suggest_optimizations(self, alerts: List[BottleneckAlert]) -> List[Dict[str, Any]]:
        """Generate optimization suggestions based on alerts"""
        suggestions = []
        
        for alert in alerts:
            if alert.component == "CPU":
                suggestions.append({
                    'type': 'configuration',
                    'target': 'skills.parallel_execution',
                    'action': 'disable',
                    'reason': 'Reduce CPU load by disabling parallel skill execution',
                    'priority': 'high'
                })
            
            elif alert.component == "Memory":
                suggestions.append({
                    'type': 'cache_cleanup',
                    'target': 'caching.llm_responses',
                    'action': 'reduce_ttl',
                    'reason': 'Reduce memory usage by shortening LLM cache TTL',
                    'priority': 'high'
                })
            
            elif alert.component == "Workflows":
                suggestions.append({
                    'type': 'caching',
                    'target': 'caching.workflow_results',
                    'action': 'enable_aggressive',
                    'reason': 'Enable aggressive workflow result caching',
                    'priority': 'medium'
                })
            
            elif alert.component == "Cache":
                suggestions.append({
                    'type': 'cache_warming',
                    'target': 'caching.optimization.preload_popular',
                    'action': 'enable',
                    'reason': 'Preload popular items to improve hit rate',
                    'priority': 'medium'
                })
        
        return suggestions
    
    async def apply_automatic_optimizations(self, suggestions: List[Dict[str, Any]]) -> List[str]:
        """Apply automatic optimizations if enabled"""
        if not self.auto_optimize:
            return []
        
        applied = []
        
        for suggestion in suggestions:
            if suggestion['priority'] == 'high':
                # Apply high-priority optimizations automatically
                try:
                    await self._apply_optimization(suggestion)
                    applied.append(f"Applied {suggestion['type']}: {suggestion['reason']}")
                    
                    self.optimization_history.append({
                        'timestamp': datetime.now(),
                        'optimization': suggestion,
                        'result': 'applied'
                    })
                except Exception as e:
                    logger.error(f"Failed to apply optimization {suggestion}: {e}")
        
        return applied
    
    async def _apply_optimization(self, suggestion: Dict[str, Any]):
        """Apply a specific optimization"""
        # This would integrate with the configuration system
        # For now, we'll just log the optimization
        logger.info(f"Would apply optimization: {suggestion}")


class RealTimePerformanceMonitor:
    """Main real-time performance monitoring system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('monitoring', {})
        self.targets = config.get('monitoring', {}).get('targets', {})
        
        self.collector = PerformanceCollector()
        self.analyzer = PerformanceAnalyzer(self.targets)
        self.optimizer = OptimizationEngine(self)
        
        self.is_running = False
        self.update_interval = self.config.get('update_interval', 1)
        self.subscribers = weakref.WeakSet()
        
        # Performance data storage
        self.current_metrics = {}
        self.performance_history = deque(maxlen=1000)
        
    async def start_monitoring(self):
        """Start real-time performance monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting real-time performance monitoring")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_running = False
        logger.info("Stopped performance monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Collect metrics
                system_metrics = await self.collector.collect_system_metrics()
                
                # Add application-specific metrics
                app_metrics = {
                    'avg_command_time': self.collector.get_avg_command_time(),
                    'cache_hit_rate': self.collector.get_cache_hit_rate(),
                    'active_websocket_users': self.collector.websocket_stats.get('active_users', 0),
                }
                
                # Combine all metrics
                all_metrics = {**system_metrics, **app_metrics}
                self.current_metrics = all_metrics
                
                # Store in history
                self.performance_history.append({
                    'timestamp': datetime.now(),
                    'metrics': all_metrics.copy()
                })
                
                # Analyze performance
                targets = self.analyzer.check_targets(all_metrics)
                alerts = self.analyzer.detect_bottlenecks(all_metrics)
                
                # Handle alerts
                if alerts:
                    await self._handle_alerts(alerts)
                
                # Notify subscribers
                await self._notify_subscribers({
                    'metrics': all_metrics,
                    'targets': [asdict(t) for t in targets],
                    'alerts': [asdict(a) for a in alerts]
                })
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def _handle_alerts(self, alerts: List[BottleneckAlert]):
        """Handle performance alerts"""
        for alert in alerts:
            logger.warning(f"Performance alert: {alert.description}")
        
        # Generate optimization suggestions
        suggestions = await self.optimizer.suggest_optimizations(alerts)
        
        # Apply automatic optimizations
        if self.config.get('auto_optimization', False):
            applied = await self.optimizer.apply_automatic_optimizations(suggestions)
            for optimization in applied:
                logger.info(f"Auto-optimization: {optimization}")
    
    async def _notify_subscribers(self, data: Dict[str, Any]):
        """Notify subscribers of performance updates"""
        for subscriber in list(self.subscribers):
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(data)
                else:
                    subscriber(data)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to performance updates"""
        self.subscribers.add(callback)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.current_metrics.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.performance_history:
            return {}
        
        recent_metrics = list(self.performance_history)[-10:]
        
        summary = {
            'monitoring_duration': time.time() - self.collector.start_time,
            'total_commands': len(self.collector.command_timings),
            'total_workflows': len(self.collector.workflow_timings),
            'current_metrics': self.current_metrics,
            'targets_status': [
                asdict(t) for t in self.analyzer.check_targets(self.current_metrics)
            ]
        }
        
        # Calculate averages from recent data
        if recent_metrics:
            avg_cpu = sum(m['metrics'].get('cpu_usage_percent', 0) for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m['metrics'].get('memory_usage_percent', 0) for m in recent_metrics) / len(recent_metrics)
            
            summary['recent_averages'] = {
                'cpu_usage': avg_cpu,
                'memory_usage': avg_memory
            }
        
        return summary
    
    # API methods for external components
    def record_command_timing(self, command: str, duration: float, success: bool = True):
        """Record command execution timing"""
        self.collector.record_command_timing(command, duration, success)
    
    def record_workflow_timing(self, workflow_id: str, duration: float, steps: int):
        """Record workflow execution timing"""
        self.collector.record_workflow_timing(workflow_id, duration, steps)
    
    def record_cache_operation(self, operation: str, hit: bool, duration: float = 0):
        """Record cache operation"""
        self.collector.record_cache_operation(operation, hit, duration)
    
    def record_websocket_activity(self, event_type: str, user_count: int):
        """Record WebSocket activity"""
        self.collector.record_websocket_activity(event_type, user_count)
