"""
Optimization Engine for Miktos AI Platform
Priority 3: Real-time Features & Optimization

Provides intelligent performance optimization, auto-tuning,
and resource management for sub-1-minute workflow execution.
"""

import asyncio
import logging
import time
import json
import psutil
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque, defaultdict
from enum import Enum
import threading
import math

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Available optimization strategies"""
    AGGRESSIVE = "aggressive"          # Maximum performance, higher resource usage
    BALANCED = "balanced"              # Balance performance and resource usage
    CONSERVATIVE = "conservative"      # Minimal resource usage, acceptable performance
    AUTO = "auto"                      # Automatic strategy selection


class ResourceType(Enum):
    """System resource types"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    CACHE = "cache"


@dataclass
class OptimizationRule:
    """Optimization rule definition"""
    name: str
    condition: str                     # Python expression to evaluate
    action: str                        # Action to take when condition is met
    parameters: Dict[str, Any]         # Parameters for the action
    priority: int                      # Higher number = higher priority
    cooldown_seconds: int              # Minimum time between applications
    last_applied: Optional[datetime] = None
    enabled: bool = True


@dataclass
class PerformanceProfile:
    """Performance profile for different scenarios"""
    name: str
    max_cpu_percent: float
    max_memory_percent: float
    max_concurrent_operations: int
    cache_aggressiveness: float        # 0.0 to 1.0
    parallelization_factor: float      # 0.0 to 1.0
    optimization_strategy: OptimizationStrategy


@dataclass
class OptimizationResult:
    """Result of an optimization operation"""
    timestamp: datetime
    rule_name: str
    action_taken: str
    parameters_changed: Dict[str, Any]
    expected_improvement: str
    success: bool
    error_message: Optional[str] = None


class ResourceMonitor:
    """Monitors system resources for optimization decisions"""
    
    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.resource_history = defaultdict(lambda: deque(maxlen=60))
        self.thresholds = {
            ResourceType.CPU: 80.0,
            ResourceType.MEMORY: 85.0,
            ResourceType.DISK: 90.0
        }
        self.is_monitoring = False
        self.monitor_task = None
    
    async def start_monitoring(self):
        """Start resource monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Resource monitoring started")
    
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect resource metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Store in history
                current_time = time.time()
                self.resource_history[ResourceType.CPU].append((current_time, cpu_percent))
                self.resource_history[ResourceType.MEMORY].append((current_time, memory.percent))
                self.resource_history[ResourceType.DISK].append((current_time, disk.percent))
                
                # Network stats if available
                try:
                    network = psutil.net_io_counters()
                    # Calculate network utilization (simplified)
                    network_util = min(100, (network.bytes_sent + network.bytes_recv) / (1024 * 1024))
                    self.resource_history[ResourceType.NETWORK].append((current_time, network_util))
                except:
                    pass
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    def get_current_usage(self) -> Dict[ResourceType, float]:
        """Get current resource usage percentages"""
        usage = {}
        
        for resource_type, history in self.resource_history.items():
            if history:
                # Get most recent value
                usage[resource_type] = history[-1][1]
            else:
                usage[resource_type] = 0.0
        
        return usage
    
    def get_average_usage(self, window_seconds: int = 60) -> Dict[ResourceType, float]:
        """Get average resource usage over time window"""
        cutoff_time = time.time() - window_seconds
        averages = {}
        
        for resource_type, history in self.resource_history.items():
            recent_values = [value for timestamp, value in history if timestamp > cutoff_time]
            if recent_values:
                averages[resource_type] = sum(recent_values) / len(recent_values)
            else:
                averages[resource_type] = 0.0
        
        return averages
    
    def get_peak_usage(self, window_seconds: int = 60) -> Dict[ResourceType, float]:
        """Get peak resource usage over time window"""
        cutoff_time = time.time() - window_seconds
        peaks = {}
        
        for resource_type, history in self.resource_history.items():
            recent_values = [value for timestamp, value in history if timestamp > cutoff_time]
            if recent_values:
                peaks[resource_type] = max(recent_values)
            else:
                peaks[resource_type] = 0.0
        
        return peaks
    
    def is_resource_constrained(self, resource_type: ResourceType) -> bool:
        """Check if a resource is currently constrained"""
        current_usage = self.get_current_usage()
        threshold = self.thresholds.get(resource_type, 100.0)
        return current_usage.get(resource_type, 0.0) > threshold


class ConfigurationTuner:
    """Automatically tunes system configuration for optimal performance"""
    
    def __init__(self, initial_config: Dict[str, Any]):
        self.base_config = initial_config.copy()
        self.current_config = initial_config.copy()
        self.config_history = []
        self.tuning_results = []
        
        # Tuning parameters
        self.tuning_enabled = True
        self.max_tuning_steps = 5
        self.performance_improvement_threshold = 0.05  # 5% improvement required
    
    async def auto_tune_configuration(self, performance_metrics: Dict[str, float],
                                    target_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Automatically tune configuration based on performance metrics"""
        if not self.tuning_enabled:
            return {}
        
        optimizations = {}
        
        # Analyze current performance vs targets
        for metric_name, target_value in target_metrics.items():
            current_value = performance_metrics.get(metric_name, 0)
            
            if metric_name == 'max_workflow_time' and current_value > target_value:
                # Workflow time too high - optimize for speed
                optimizations.update(await self._optimize_workflow_speed())
            
            elif metric_name == 'min_cache_hit_rate' and current_value < target_value:
                # Cache hit rate too low - optimize caching
                optimizations.update(await self._optimize_caching())
            
            elif metric_name == 'max_cpu_usage' and current_value > target_value:
                # CPU usage too high - reduce parallelization
                optimizations.update(await self._optimize_cpu_usage())
            
            elif metric_name == 'max_memory_usage' and current_value > target_value:
                # Memory usage too high - optimize memory
                optimizations.update(await self._optimize_memory_usage())
        
        # Apply optimizations
        if optimizations:
            await self._apply_configuration_changes(optimizations)
        
        return optimizations
    
    async def _optimize_workflow_speed(self) -> Dict[str, Any]:
        """Optimize configuration for faster workflow execution"""
        optimizations = {}
        
        # Enable more aggressive caching
        optimizations['caching.llm_responses.ttl'] = min(
            self.current_config.get('caching', {}).get('llm_responses', {}).get('ttl', 3600) * 2,
            7200  # Max 2 hours
        )
        
        # Increase parallel operations if resources allow
        current_parallel = self.current_config.get('skills', {}).get('max_parallel', 2)
        optimizations['skills.max_parallel'] = min(current_parallel + 1, 4)
        
        # Enable workflow result caching
        optimizations['caching.workflow_results.enabled'] = True
        optimizations['caching.workflow_results.ttl'] = 1800  # 30 minutes
        
        return optimizations
    
    async def _optimize_caching(self) -> Dict[str, Any]:
        """Optimize caching configuration"""
        optimizations = {}
        
        # Increase cache sizes
        current_memory_cache = self.current_config.get('caching', {}).get('memory_cache', {})
        optimizations['caching.memory_cache.max_entries'] = min(
            current_memory_cache.get('max_entries', 1000) * 1.5,
            2000
        )
        optimizations['caching.memory_cache.max_memory_mb'] = min(
            current_memory_cache.get('max_memory_mb', 512) * 1.5,
            1024
        )
        
        # Enable cache warming
        optimizations['caching.warming.enabled'] = True
        optimizations['caching.warming.preload_popular'] = True
        
        # Increase TTL for stable data
        optimizations['caching.llm_responses.ttl'] = 7200  # 2 hours
        
        return optimizations
    
    async def _optimize_cpu_usage(self) -> Dict[str, Any]:
        """Optimize configuration to reduce CPU usage"""
        optimizations = {}
        
        # Reduce parallel operations
        current_parallel = self.current_config.get('skills', {}).get('max_parallel', 2)
        optimizations['skills.max_parallel'] = max(current_parallel - 1, 1)
        
        # Disable parallel execution if enabled
        optimizations['skills.parallel_execution'] = False
        
        # Reduce monitoring frequency
        optimizations['monitoring.update_interval'] = 2  # 2 seconds instead of 1
        
        return optimizations
    
    async def _optimize_memory_usage(self) -> Dict[str, Any]:
        """Optimize configuration to reduce memory usage"""
        optimizations = {}
        
        # Reduce cache sizes
        current_memory_cache = self.current_config.get('caching', {}).get('memory_cache', {})
        optimizations['caching.memory_cache.max_entries'] = max(
            int(current_memory_cache.get('max_entries', 1000) * 0.7),
            500
        )
        optimizations['caching.memory_cache.max_memory_mb'] = max(
            int(current_memory_cache.get('max_memory_mb', 512) * 0.7),
            256
        )
        
        # Reduce TTL to free memory faster
        optimizations['caching.llm_responses.ttl'] = 1800  # 30 minutes
        
        # Disable some caching features
        optimizations['caching.workflow_results.enabled'] = False
        
        return optimizations
    
    async def _apply_configuration_changes(self, optimizations: Dict[str, Any]):
        """Apply configuration changes"""
        # Store current config in history
        self.config_history.append({
            'timestamp': datetime.now(),
            'config': self.current_config.copy(),
            'optimizations': optimizations.copy()
        })
        
        # Apply changes to current config
        for key, value in optimizations.items():
            self._set_nested_config(self.current_config, key, value)
        
        logger.info(f"Applied {len(optimizations)} configuration optimizations")
    
    def _set_nested_config(self, config: Dict[str, Any], key: str, value: Any):
        """Set nested configuration value using dot notation"""
        parts = key.split('.')
        current = config
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.current_config.copy()
    
    def revert_to_base_config(self):
        """Revert to base configuration"""
        self.current_config = self.base_config.copy()
        logger.info("Reverted to base configuration")


class WorkflowOptimizer:
    """Optimizes workflow execution patterns"""
    
    def __init__(self):
        self.workflow_stats = defaultdict(lambda: {
            'executions': 0,
            'total_time': 0.0,
            'success_rate': 0.0,
            'avg_steps': 0,
            'bottlenecks': []
        })
        
        self.optimization_patterns = [
            self._optimize_step_order,
            self._optimize_parallelization,
            self._optimize_caching_strategy,
            self._optimize_resource_allocation
        ]
    
    async def analyze_workflow(self, workflow_id: str, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workflow execution for optimization opportunities"""
        stats = self.workflow_stats[workflow_id]
        
        # Update statistics with type safety
        executions = stats.get('executions', 0)
        if isinstance(executions, (int, float)):
            stats['executions'] = int(executions) + 1
        else:
            stats['executions'] = 1
        
        total_time = stats.get('total_time', 0.0)
        if isinstance(total_time, (int, float)):
            stats['total_time'] = float(total_time) + execution_data.get('duration', 0)
        else:
            stats['total_time'] = execution_data.get('duration', 0)
        
        success_rate = stats.get('success_rate', 0.0)
        if isinstance(success_rate, (int, float)) and isinstance(stats['executions'], int):
            if execution_data.get('success', False):
                stats['success_rate'] = (float(success_rate) * (stats['executions'] - 1) + 1) / stats['executions']
            else:
                stats['success_rate'] = (float(success_rate) * (stats['executions'] - 1)) / stats['executions']
        else:
            stats['success_rate'] = 1.0 if execution_data.get('success', False) else 0.0
        
        avg_steps = stats.get('avg_steps', 0)
        if isinstance(avg_steps, (int, float)):
            stats['avg_steps'] = execution_data.get('steps', int(avg_steps))
        else:
            stats['avg_steps'] = execution_data.get('steps', 0)
        
        # Identify bottlenecks
        step_timings = execution_data.get('step_timings', [])
        if step_timings:
            # Find steps taking more than 20% of total time
            total_time = sum(step_timings)
            bottlenecks = [
                i for i, timing in enumerate(step_timings)
                if timing > total_time * 0.2
            ]
            stats['bottlenecks'] = bottlenecks
        
        # Generate optimization suggestions
        suggestions = []
        for optimizer in self.optimization_patterns:
            try:
                suggestion = await optimizer(workflow_id, stats, execution_data)
                if suggestion:
                    suggestions.append(suggestion)
            except Exception as e:
                logger.error(f"Optimization pattern error: {e}")
        
        return {
            'workflow_id': workflow_id,
            'stats': stats,
            'suggestions': suggestions
        }
    
    async def _optimize_step_order(self, workflow_id: str, stats: Dict[str, Any],
                                 execution_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Suggest step order optimizations"""
        step_timings = execution_data.get('step_timings', [])
        if len(step_timings) < 3:
            return None
        
        # Look for expensive steps that could be moved earlier for early failure
        expensive_steps = [
            i for i, timing in enumerate(step_timings)
            if timing > sum(step_timings) * 0.3
        ]
        
        if expensive_steps and expensive_steps[0] > len(step_timings) * 0.5:
            return {
                'type': 'step_reordering',
                'description': 'Move expensive steps earlier to fail fast',
                'expected_improvement': '15-30% faster failure detection',
                'parameters': {
                    'move_steps': expensive_steps,
                    'target_position': 'early'
                }
            }
        
        return None
    
    async def _optimize_parallelization(self, workflow_id: str, stats: Dict[str, Any],
                                      execution_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Suggest parallelization opportunities"""
        step_dependencies = execution_data.get('step_dependencies', [])
        if not step_dependencies:
            return None
        
        # Find independent steps that could run in parallel
        independent_groups = self._find_independent_steps(step_dependencies)
        
        if len(independent_groups) > 1:
            return {
                'type': 'parallelization',
                'description': f'Run {len(independent_groups)} step groups in parallel',
                'expected_improvement': '20-50% faster execution',
                'parameters': {
                    'parallel_groups': independent_groups
                }
            }
        
        return None
    
    async def _optimize_caching_strategy(self, workflow_id: str, stats: Dict[str, Any],
                                       execution_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Suggest caching optimizations"""
        repeated_operations = execution_data.get('repeated_operations', [])
        
        if repeated_operations:
            return {
                'type': 'caching',
                'description': f'Cache {len(repeated_operations)} repeated operations',
                'expected_improvement': '30-60% faster for repeated executions',
                'parameters': {
                    'cache_operations': repeated_operations,
                    'ttl': 3600  # 1 hour
                }
            }
        
        return None
    
    async def _optimize_resource_allocation(self, workflow_id: str, stats: Dict[str, Any],
                                          execution_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Suggest resource allocation optimizations"""
        resource_usage = execution_data.get('resource_usage', {})
        if not resource_usage:
            return None
        
        # Check for resource imbalances
        cpu_usage = resource_usage.get('cpu_peak', 0)
        memory_usage = resource_usage.get('memory_peak', 0)
        
        if cpu_usage > 80 and memory_usage < 50:
            return {
                'type': 'resource_allocation',
                'description': 'CPU-bound workflow, reduce parallelization',
                'expected_improvement': '10-20% better resource utilization',
                'parameters': {
                    'reduce_parallel_operations': True,
                    'target_cpu_usage': 70
                }
            }
        elif memory_usage > 80 and cpu_usage < 50:
            return {
                'type': 'resource_allocation',
                'description': 'Memory-bound workflow, increase caching efficiency',
                'expected_improvement': '15-25% better memory utilization',
                'parameters': {
                    'optimize_memory_caching': True,
                    'target_memory_usage': 70
                }
            }
        
        return None
    
    def _find_independent_steps(self, dependencies: List[List[int]]) -> List[List[int]]:
        """Find groups of independent steps that can run in parallel"""
        # Simplified dependency analysis
        # In a real implementation, this would use graph algorithms
        independent_groups = []
        
        # For now, just return groups of steps without dependencies
        used_steps = set()
        for i, deps in enumerate(dependencies):
            if not deps and i not in used_steps:
                group = [i]
                # Find other steps with no dependencies
                for j, other_deps in enumerate(dependencies[i+1:], i+1):
                    if not other_deps and j not in used_steps:
                        group.append(j)
                
                if len(group) > 1:
                    independent_groups.append(group)
                    used_steps.update(group)
        
        return independent_groups


class OptimizationEngine:
    """Main optimization engine coordinating all optimization components"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('optimization', {})
        
        # Initialize components
        self.resource_monitor = ResourceMonitor(
            monitoring_interval=self.config.get('monitoring_interval', 1.0)
        )
        
        self.config_tuner = ConfigurationTuner(config)
        self.workflow_optimizer = WorkflowOptimizer()
        
        # Optimization settings
        self.strategy = OptimizationStrategy(self.config.get('strategy', 'balanced'))
        self.auto_optimize = self.config.get('auto_optimize', True)
        self.optimization_interval = self.config.get('optimization_interval', 300)  # 5 minutes
        
        # Performance profiles
        self.performance_profiles = self._load_performance_profiles()
        self.current_profile = self.performance_profiles.get('balanced')
        
        # Optimization rules
        self.optimization_rules = self._load_optimization_rules()
        
        # Results tracking
        self.optimization_history = deque(maxlen=100)
        self.is_running = False
        
        # Performance monitoring integration
        self.performance_monitor = None
        self.cache_manager = None
    
    def set_performance_monitor(self, monitor):
        """Set performance monitor for integration"""
        self.performance_monitor = monitor
    
    def set_cache_manager(self, cache_manager):
        """Set cache manager for optimization"""
        self.cache_manager = cache_manager
    
    async def start_optimization(self):
        """Start the optimization engine"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting optimization engine")
        
        # Start resource monitoring
        await self.resource_monitor.start_monitoring()
        
        # Start optimization loop
        asyncio.create_task(self._optimization_loop())
    
    async def stop_optimization(self):
        """Stop the optimization engine"""
        self.is_running = False
        
        # Stop resource monitoring
        await self.resource_monitor.stop_monitoring()
        
        logger.info("Stopped optimization engine")
    
    async def _optimization_loop(self):
        """Main optimization loop"""
        while self.is_running:
            try:
                if self.auto_optimize:
                    await self._run_optimization_cycle()
                
                await asyncio.sleep(self.optimization_interval)
                
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(60)
    
    async def _run_optimization_cycle(self):
        """Run a complete optimization cycle"""
        logger.debug("Running optimization cycle")
        
        # Collect performance metrics
        performance_metrics = await self._collect_performance_metrics()
        
        # Apply optimization rules
        rule_results = await self._apply_optimization_rules(performance_metrics)
        
        # Auto-tune configuration
        config_optimizations = await self.config_tuner.auto_tune_configuration(
            performance_metrics,
            self._get_performance_targets()
        )
        
        # Record results
        if rule_results or config_optimizations:
            self.optimization_history.append({
                'timestamp': datetime.now(),
                'performance_metrics': performance_metrics,
                'rule_results': rule_results,
                'config_optimizations': config_optimizations
            })
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive performance metrics"""
        metrics = {}
        
        # System resource metrics
        metrics.update(self.resource_monitor.get_current_usage())
        metrics.update({
            f"avg_{k.value}": v for k, v in self.resource_monitor.get_average_usage().items()
        })
        
        # Application metrics from performance monitor
        if self.performance_monitor:
            app_metrics = self.performance_monitor.get_current_metrics()
            metrics.update(app_metrics)
        
        # Cache metrics
        if self.cache_manager:
            cache_stats = self.cache_manager.get_stats()
            if 'memory_cache' in cache_stats:
                metrics['cache_hit_rate'] = cache_stats['memory_cache'].get('hit_rate', 0)
                metrics['cache_entry_count'] = cache_stats['memory_cache'].get('entry_count', 0)
        
        return metrics
    
    async def _apply_optimization_rules(self, metrics: Dict[str, Any]) -> List[OptimizationResult]:
        """Apply optimization rules based on current metrics"""
        results = []
        current_time = datetime.now()
        
        for rule in sorted(self.optimization_rules, key=lambda r: r.priority, reverse=True):
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule.last_applied:
                time_since_applied = (current_time - rule.last_applied).total_seconds()
                if time_since_applied < rule.cooldown_seconds:
                    continue
            
            # Evaluate condition
            try:
                condition_met = eval(rule.condition, {"metrics": metrics, "math": math})
                if condition_met:
                    result = await self._execute_optimization_action(rule, metrics)
                    results.append(result)
                    
                    if result.success:
                        rule.last_applied = current_time
            
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")
                results.append(OptimizationResult(
                    timestamp=current_time,
                    rule_name=rule.name,
                    action_taken=rule.action,
                    parameters_changed={},
                    expected_improvement="",
                    success=False,
                    error_message=str(e)
                ))
        
        return results
    
    async def _execute_optimization_action(self, rule: OptimizationRule,
                                         metrics: Dict[str, Any]) -> OptimizationResult:
        """Execute optimization action"""
        current_time = datetime.now()
        
        try:
            action_params = rule.parameters.copy()
            
            if rule.action == "reduce_parallel_operations":
                # Reduce number of parallel operations
                current_parallel = self.config_tuner.current_config.get('skills', {}).get('max_parallel', 2)
                new_parallel = max(1, current_parallel - 1)
                
                await self.config_tuner._apply_configuration_changes({
                    'skills.max_parallel': new_parallel
                })
                
                return OptimizationResult(
                    timestamp=current_time,
                    rule_name=rule.name,
                    action_taken=rule.action,
                    parameters_changed={'max_parallel': new_parallel},
                    expected_improvement="Reduced CPU load",
                    success=True
                )
            
            elif rule.action == "increase_cache_size":
                # Increase cache size
                current_size = self.config_tuner.current_config.get('caching', {}).get('memory_cache', {}).get('max_entries', 1000)
                new_size = min(current_size * 1.2, 2000)
                
                await self.config_tuner._apply_configuration_changes({
                    'caching.memory_cache.max_entries': int(new_size)
                })
                
                return OptimizationResult(
                    timestamp=current_time,
                    rule_name=rule.name,
                    action_taken=rule.action,
                    parameters_changed={'cache_max_entries': int(new_size)},
                    expected_improvement="Improved cache hit rate",
                    success=True
                )
            
            elif rule.action == "enable_aggressive_caching":
                # Enable more aggressive caching
                await self.config_tuner._apply_configuration_changes({
                    'caching.llm_responses.ttl': 7200,  # 2 hours
                    'caching.workflow_results.enabled': True,
                    'caching.warming.enabled': True
                })
                
                return OptimizationResult(
                    timestamp=current_time,
                    rule_name=rule.name,
                    action_taken=rule.action,
                    parameters_changed={
                        'llm_cache_ttl': 7200,
                        'workflow_cache_enabled': True,
                        'cache_warming_enabled': True
                    },
                    expected_improvement="Faster response times",
                    success=True
                )
            
            else:
                return OptimizationResult(
                    timestamp=current_time,
                    rule_name=rule.name,
                    action_taken=rule.action,
                    parameters_changed={},
                    expected_improvement="",
                    success=False,
                    error_message=f"Unknown action: {rule.action}"
                )
        
        except Exception as e:
            return OptimizationResult(
                timestamp=current_time,
                rule_name=rule.name,
                action_taken=rule.action,
                parameters_changed={},
                expected_improvement="",
                success=False,
                error_message=str(e)
            )
    
    def _get_performance_targets(self) -> Dict[str, float]:
        """Get performance targets based on current profile"""
        if not self.current_profile:
            return {}
        
        return {
            'max_workflow_time': 60.0,  # Sub-1-minute target
            'min_cache_hit_rate': 0.8,  # 80% hit rate
            'max_cpu_usage': self.current_profile.max_cpu_percent,
            'max_memory_usage': self.current_profile.max_memory_percent
        }
    
    def _load_performance_profiles(self) -> Dict[str, PerformanceProfile]:
        """Load performance profiles"""
        return {
            'aggressive': PerformanceProfile(
                name='aggressive',
                max_cpu_percent=95.0,
                max_memory_percent=90.0,
                max_concurrent_operations=8,
                cache_aggressiveness=1.0,
                parallelization_factor=1.0,
                optimization_strategy=OptimizationStrategy.AGGRESSIVE
            ),
            'balanced': PerformanceProfile(
                name='balanced',
                max_cpu_percent=80.0,
                max_memory_percent=75.0,
                max_concurrent_operations=4,
                cache_aggressiveness=0.7,
                parallelization_factor=0.8,
                optimization_strategy=OptimizationStrategy.BALANCED
            ),
            'conservative': PerformanceProfile(
                name='conservative',
                max_cpu_percent=60.0,
                max_memory_percent=60.0,
                max_concurrent_operations=2,
                cache_aggressiveness=0.5,
                parallelization_factor=0.5,
                optimization_strategy=OptimizationStrategy.CONSERVATIVE
            )
        }
    
    def _load_optimization_rules(self) -> List[OptimizationRule]:
        """Load optimization rules"""
        return [
            OptimizationRule(
                name="high_cpu_usage",
                condition="metrics.get('cpu_usage_percent', 0) > 85",
                action="reduce_parallel_operations",
                parameters={'reduction_factor': 0.5},
                priority=10,
                cooldown_seconds=300
            ),
            OptimizationRule(
                name="low_cache_hit_rate",
                condition="metrics.get('cache_hit_rate', 1.0) < 0.6",
                action="increase_cache_size",
                parameters={'size_multiplier': 1.5},
                priority=8,
                cooldown_seconds=600
            ),
            OptimizationRule(
                name="slow_workflow_execution",
                condition="metrics.get('avg_workflow_time', 0) > 60",
                action="enable_aggressive_caching",
                parameters={},
                priority=7,
                cooldown_seconds=900
            ),
            OptimizationRule(
                name="high_memory_usage",
                condition="metrics.get('memory_usage_percent', 0) > 85",
                action="reduce_cache_size",
                parameters={'reduction_factor': 0.8},
                priority=9,
                cooldown_seconds=300
            )
        ]
    
    async def optimize_workflow(self, workflow_id: str, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize specific workflow"""
        return await self.workflow_optimizer.analyze_workflow(workflow_id, execution_data)
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status"""
        return {
            'is_running': self.is_running,
            'strategy': self.strategy.value,
            'current_profile': self.current_profile.name if self.current_profile else None,
            'auto_optimize': self.auto_optimize,
            'resource_usage': self.resource_monitor.get_current_usage(),
            'recent_optimizations': len(self.optimization_history),
            'rules_enabled': sum(1 for rule in self.optimization_rules if rule.enabled)
        }
    
    def get_optimization_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent optimization history"""
        return list(self.optimization_history)[-limit:]
    
    async def set_optimization_strategy(self, strategy: OptimizationStrategy):
        """Set optimization strategy"""
        self.strategy = strategy
        self.current_profile = self.performance_profiles.get(strategy.value, self.current_profile)
        logger.info(f"Set optimization strategy to {strategy.value}")
    
    def enable_auto_optimization(self, enabled: bool = True):
        """Enable or disable automatic optimization"""
        self.auto_optimize = enabled
        logger.info(f"Auto-optimization {'enabled' if enabled else 'disabled'}")
