"""
Result Analyzer for Miktos AI Bridge Platform

Analyzes operation results to extract insights, detect issues,
and provide feedback for learning and optimization.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import statistics


class ResultStatus(Enum):
    """Status of operation result."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    WARNING = "warning"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class PerformanceMetrics:
    """Performance metrics for an operation."""
    execution_time: float
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    blender_response_time: Optional[float] = None
    viewer_update_time: Optional[float] = None


@dataclass
class OperationResult:
    """Result of a Blender operation."""
    operation: str
    status: ResultStatus
    message: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    blender_output: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Optional[PerformanceMetrics] = None
    timestamp: datetime = field(default_factory=datetime.now)
    objects_created: List[str] = field(default_factory=list)
    objects_modified: List[str] = field(default_factory=list)
    objects_deleted: List[str] = field(default_factory=list)


@dataclass
class AnalysisInsight:
    """Insight extracted from result analysis."""
    category: str
    insight_type: str
    description: str
    impact: str  # "positive", "negative", "neutral"
    confidence: float  # 0.0 to 1.0
    suggestions: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Comprehensive analysis result for operation."""
    operation: str
    status: ResultStatus
    insights: List[AnalysisInsight] = field(default_factory=list)
    performance_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    overall_assessment: str = ""


class ResultAnalyzer:
    """
    Analyzes operation results to provide insights and feedback.
    
    Responsibilities:
    - Analyze operation success/failure patterns
    - Extract performance insights
    - Detect optimization opportunities
    - Generate learning feedback
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger('ResultAnalyzer')
        
        # Analysis settings
        self.enable_detailed_analysis = self.config.get('enable_detailed_analysis', True)
        self.performance_threshold_ms = self.config.get('performance_threshold_ms', 1000)
        self.error_pattern_tracking = self.config.get('error_pattern_tracking', True)
        
        # Result history for pattern analysis
        self.result_history: List[OperationResult] = []
        self.max_history_size = self.config.get('max_history_size', 1000)
        
        # Performance baselines
        self.performance_baselines: Dict[str, float] = {}
        self.error_patterns: Dict[str, int] = {}
        
        # Analysis cache
        self.insight_cache: Dict[str, List[AnalysisInsight]] = {}
        self.cache_ttl_seconds = self.config.get('cache_ttl_seconds', 300)
    
    async def analyze_result(self, result: OperationResult) -> List[AnalysisInsight]:
        """
        Analyze a single operation result and extract insights.
        
        Args:
            result: Operation result to analyze
            
        Returns:
            List of insights extracted from the result
        """
        try:
            # Add to history
            self._add_to_history(result)
            
            insights = []
            
            # Performance analysis
            if result.metrics:
                perf_insights = await self._analyze_performance(result)
                insights.extend(perf_insights)
            
            # Error analysis
            if result.errors or result.status == ResultStatus.ERROR:
                error_insights = await self._analyze_errors(result)
                insights.extend(error_insights)
            
            # Success pattern analysis
            if result.status == ResultStatus.SUCCESS:
                success_insights = await self._analyze_success_patterns(result)
                insights.extend(success_insights)
            
            # Parameter optimization insights
            if self.enable_detailed_analysis:
                param_insights = await self._analyze_parameters(result)
                insights.extend(param_insights)
            
            # Output quality analysis
            output_insights = await self._analyze_output_quality(result)
            insights.extend(output_insights)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to analyze result: {e}")
            return []
    
    async def _analyze_performance(self, result: OperationResult) -> List[AnalysisInsight]:
        """Analyze performance metrics."""
        insights = []
        metrics = result.metrics
        
        if not metrics:
            return insights
        
        # Execution time analysis
        exec_time_ms = metrics.execution_time * 1000
        
        # Get baseline for this operation
        baseline = self.performance_baselines.get(result.operation)
        if baseline is None:
            # Establish baseline
            self.performance_baselines[result.operation] = exec_time_ms
            insights.append(AnalysisInsight(
                category="performance",
                insight_type="baseline_established",
                description=f"Performance baseline established for {result.operation}: {exec_time_ms:.1f}ms",
                impact="neutral",
                confidence=0.8
            ))
        else:
            # Compare to baseline
            improvement_ratio = (baseline - exec_time_ms) / baseline
            
            if improvement_ratio > 0.2:  # 20% improvement
                insights.append(AnalysisInsight(
                    category="performance",
                    insight_type="performance_improved",
                    description=f"Operation {result.operation} performed {improvement_ratio:.1%} faster than baseline",
                    impact="positive",
                    confidence=0.9,
                    suggestions=["Consider if parameter changes contributed to improvement"]
                ))
            elif improvement_ratio < -0.5:  # 50% slower
                insights.append(AnalysisInsight(
                    category="performance",
                    insight_type="performance_degraded",
                    description=f"Operation {result.operation} performed {abs(improvement_ratio):.1%} slower than baseline",
                    impact="negative",
                    confidence=0.9,
                    suggestions=[
                        "Check if complex parameters were used",
                        "Consider system resource availability",
                        "Review parameter efficiency"
                    ]
                ))
            
            # Update baseline with moving average
            self.performance_baselines[result.operation] = (baseline * 0.8 + exec_time_ms * 0.2)
        
        # Absolute performance thresholds
        if exec_time_ms > self.performance_threshold_ms:
            insights.append(AnalysisInsight(
                category="performance",
                insight_type="slow_execution",
                description=f"Operation took {exec_time_ms:.1f}ms (above {self.performance_threshold_ms}ms threshold)",
                impact="negative",
                confidence=0.8,
                suggestions=[
                    "Consider simplifying parameters",
                    "Check system performance",
                    "Break complex operations into smaller steps"
                ]
            ))
        
        # Memory usage analysis
        if metrics.memory_usage_mb and metrics.memory_usage_mb > 100:
            insights.append(AnalysisInsight(
                category="performance",
                insight_type="high_memory_usage",
                description=f"Operation used {metrics.memory_usage_mb:.1f}MB of memory",
                impact="negative",
                confidence=0.7,
                suggestions=["Consider memory optimization techniques"]
            ))
        
        return insights
    
    async def _analyze_errors(self, result: OperationResult) -> List[AnalysisInsight]:
        """Analyze error patterns and provide insights."""
        insights = []
        
        for error in result.errors:
            # Track error patterns
            if self.error_pattern_tracking:
                error_key = self._normalize_error(error)
                self.error_patterns[error_key] = self.error_patterns.get(error_key, 0) + 1
                
                # Detect recurring errors
                if self.error_patterns[error_key] > 3:
                    insights.append(AnalysisInsight(
                        category="error",
                        insight_type="recurring_error",
                        description=f"Error pattern detected {self.error_patterns[error_key]} times: {error_key}",
                        impact="negative",
                        confidence=0.9,
                        suggestions=[
                            "Review parameter validation",
                            "Check operation prerequisites",
                            "Consider alternative approach"
                        ]
                    ))
            
            # Specific error analysis
            if "parameter" in error.lower():
                insights.append(AnalysisInsight(
                    category="error",
                    insight_type="parameter_error",
                    description="Parameter-related error detected",
                    impact="negative",
                    confidence=0.8,
                    suggestions=[
                        "Validate parameter types and ranges",
                        "Check parameter documentation",
                        "Use default values for testing"
                    ]
                ))
            
            elif "connection" in error.lower() or "socket" in error.lower():
                insights.append(AnalysisInsight(
                    category="error",
                    insight_type="connection_error",
                    description="Blender connection issue detected",
                    impact="negative",
                    confidence=0.9,
                    suggestions=[
                        "Check Blender is running",
                        "Verify socket connection",
                        "Restart Blender bridge"
                    ]
                ))
            
            elif "timeout" in error.lower():
                insights.append(AnalysisInsight(
                    category="error",
                    insight_type="timeout_error",
                    description="Operation timeout detected",
                    impact="negative",
                    confidence=0.8,
                    suggestions=[
                        "Increase timeout threshold",
                        "Simplify operation complexity",
                        "Check system performance"
                    ]
                ))
        
        return insights
    
    async def _analyze_success_patterns(self, result: OperationResult) -> List[AnalysisInsight]:
        """Analyze successful operations for patterns."""
        insights = []
        
        # Quick success analysis
        if result.metrics and result.metrics.execution_time < 0.1:  # Very fast
            insights.append(AnalysisInsight(
                category="success",
                insight_type="efficient_execution",
                description=f"Operation {result.operation} completed very efficiently ({result.metrics.execution_time:.3f}s)",
                impact="positive",
                confidence=0.8
            ))
        
        # Object creation success
        if result.objects_created:
            insights.append(AnalysisInsight(
                category="success",
                insight_type="object_creation",
                description=f"Successfully created {len(result.objects_created)} object(s)",
                impact="positive",
                confidence=1.0
            ))
        
        # Complex operation success
        if len(result.parameters) > 5:  # Many parameters
            insights.append(AnalysisInsight(
                category="success",
                insight_type="complex_operation_success",
                description="Successfully executed complex operation with multiple parameters",
                impact="positive",
                confidence=0.9,
                suggestions=["Consider saving successful parameter combinations"]
            ))
        
        return insights
    
    async def _analyze_parameters(self, result: OperationResult) -> List[AnalysisInsight]:
        """Analyze parameter usage patterns."""
        insights = []
        
        # Default parameter usage
        default_params = self._count_default_parameters(result.parameters)
        if default_params > len(result.parameters) * 0.8:  # 80% defaults
            insights.append(AnalysisInsight(
                category="parameters",
                insight_type="heavy_default_usage",
                description="Operation relies heavily on default parameters",
                impact="neutral",
                confidence=0.7,
                suggestions=["Consider customizing parameters for better results"]
            ))
        
        # Parameter complexity analysis
        complex_params = self._count_complex_parameters(result.parameters)
        if complex_params > 0:
            insights.append(AnalysisInsight(
                category="parameters",
                insight_type="complex_parameters",
                description=f"Operation uses {complex_params} complex parameter(s)",
                impact="neutral",
                confidence=0.8,
                suggestions=["Monitor performance impact of complex parameters"]
            ))
        
        # Parameter optimization suggestions
        optimization_suggestions = self._get_parameter_optimizations(result.operation, result.parameters)
        if optimization_suggestions:
            insights.append(AnalysisInsight(
                category="parameters",
                insight_type="optimization_opportunity",
                description="Parameter optimization opportunities detected",
                impact="positive",
                confidence=0.6,
                suggestions=optimization_suggestions
            ))
        
        return insights
    
    async def _analyze_output_quality(self, result: OperationResult) -> List[AnalysisInsight]:
        """Analyze the quality of operation output."""
        insights = []
        
        # Blender output analysis
        if result.blender_output:
            # Check for warnings in Blender output
            blender_warnings = result.blender_output.get('warnings', [])
            if blender_warnings:
                insights.append(AnalysisInsight(
                    category="output",
                    insight_type="blender_warnings",
                    description=f"Blender reported {len(blender_warnings)} warning(s)",
                    impact="negative",
                    confidence=0.7,
                    suggestions=["Review Blender warnings for potential issues"]
                ))
            
            # Check object count changes
            objects_affected = len(result.objects_created) + len(result.objects_modified) + len(result.objects_deleted)
            if objects_affected == 0 and result.status == ResultStatus.SUCCESS:
                insights.append(AnalysisInsight(
                    category="output",
                    insight_type="no_visible_changes",
                    description="Operation completed successfully but no objects were affected",
                    impact="neutral",
                    confidence=0.8,
                    suggestions=["Verify operation parameters and intended effect"]
                ))
        
        return insights
    
    def _add_to_history(self, result: OperationResult):
        """Add result to history with size management."""
        self.result_history.append(result)
        
        # Maintain history size
        while len(self.result_history) > self.max_history_size:
            self.result_history.pop(0)
    
    def _normalize_error(self, error: str) -> str:
        """Normalize error message for pattern detection."""
        # Remove specific values and keep error pattern
        import re
        
        # Remove numbers
        normalized = re.sub(r'\d+\.?\d*', 'N', error)
        
        # Remove specific names
        normalized = re.sub(r'"[^"]*"', '"NAME"', normalized)
        normalized = re.sub(r"'[^']*'", "'NAME'", normalized)
        
        # Remove file paths
        normalized = re.sub(r'/[^\s]*', '/PATH', normalized)
        
        return normalized.lower()
    
    def _count_default_parameters(self, parameters: Dict[str, Any]) -> int:
        """Count parameters that are likely using default values."""
        default_count = 0
        common_defaults = {
            'location': [0, 0, 0],
            'rotation': [0, 0, 0],
            'scale': [1, 1, 1],
            'size': 1.0,
            'radius': 1.0,
            'height': 2.0
        }
        
        for param, value in parameters.items():
            if param in common_defaults and value == common_defaults[param]:
                default_count += 1
        
        return default_count
    
    def _count_complex_parameters(self, parameters: Dict[str, Any]) -> int:
        """Count complex parameters (lists, dicts, etc.)."""
        complex_count = 0
        for value in parameters.values():
            if isinstance(value, (list, dict, tuple)) and len(str(value)) > 10:
                complex_count += 1
        return complex_count
    
    def _get_parameter_optimizations(self, operation: str, parameters: Dict[str, Any]) -> List[str]:
        """Get parameter optimization suggestions."""
        suggestions = []
        
        # Operation-specific optimizations
        if operation.startswith('create_') and 'subdivisions' in parameters:
            subdivisions = parameters['subdivisions']
            if isinstance(subdivisions, int) and subdivisions > 3:
                suggestions.append("Consider reducing subdivisions for better performance")
        
        if 'scale' in parameters:
            scale = parameters['scale']
            if isinstance(scale, (list, tuple)) and all(s == scale[0] for s in scale):
                suggestions.append("Use single scale value instead of uniform list")
        
        return suggestions
    
    async def get_operation_statistics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for operations."""
        if operation:
            results = [r for r in self.result_history if r.operation == operation]
        else:
            results = self.result_history
        
        if not results:
            return {}
        
        # Calculate statistics
        success_count = sum(1 for r in results if r.status == ResultStatus.SUCCESS)
        error_count = sum(1 for r in results if r.status == ResultStatus.ERROR)
        
        execution_times = [r.metrics.execution_time for r in results if r.metrics]
        
        stats = {
            'total_operations': len(results),
            'success_rate': success_count / len(results) if results else 0,
            'error_rate': error_count / len(results) if results else 0,
            'average_execution_time': statistics.mean(execution_times) if execution_times else 0,
            'median_execution_time': statistics.median(execution_times) if execution_times else 0
        }
        
        if execution_times:
            stats['min_execution_time'] = min(execution_times)
            stats['max_execution_time'] = max(execution_times)
        
        return stats
    
    async def get_error_summary(self) -> Dict[str, int]:
        """Get summary of error patterns."""
        return dict(self.error_patterns)
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        total_operations = len(self.result_history)
        if not total_operations:
            return {"message": "No operations recorded"}
        
        # Overall statistics
        recent_results = self.result_history[-100:]  # Last 100 operations
        
        report = {
            'summary': {
                'total_operations': total_operations,
                'recent_operations': len(recent_results),
                'operation_types': len(set(r.operation for r in self.result_history))
            },
            'performance': await self.get_operation_statistics(),
            'error_patterns': await self.get_error_summary(),
            'baselines': dict(self.performance_baselines)
        }
        
        return report
    
    def clear_history(self):
        """Clear analysis history."""
        self.result_history.clear()
        self.error_patterns.clear()
        self.insight_cache.clear()
        self.logger.debug("Analysis history cleared")
