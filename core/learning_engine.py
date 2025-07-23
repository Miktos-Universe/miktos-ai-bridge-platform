"""
Learning Engine for Miktos Agent

Implements reinforcement learning and continuous improvement capabilities
for the AI agent, optimizing command execution and skill selection.
"""

import asyncio
import json
import logging
import pickle
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass

# Import shared types from agent module
from .agent import AgentCommand, ExecutionResult

# Import typing for type hints that don't cause circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass  # Can import additional types here if needed

import json
import logging
import asyncio
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path


# Import type definitions
@dataclass
class ParsedCommand:
    """Represents a fully parsed command ready for execution"""
    original_text: str
    primary_intent: str
    target_object: str
    parameters: Dict[str, Any]
    intents: List[Any]
    confidence: float
    execution_complexity: float
    required_skills: List[str]
    dependencies: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SkillPerformance:
    """Tracks performance metrics for a skill"""
    skill_name: str
    success_rate: float
    average_execution_time: float
    usage_count: int
    error_patterns: List[str]
    parameter_effectiveness: Dict[str, float]
    last_updated: datetime
    confidence_score: float = 0.8


@dataclass
class UserPreference:
    """Represents a learned user preference"""
    preference_type: str  # "parameter", "style", "workflow"
    context: str
    preferred_value: Any
    confidence: float
    usage_count: int
    last_seen: datetime


@dataclass
class LearningInsight:
    """Represents a learning insight or pattern"""
    insight_type: str  # "optimization", "preference", "pattern", "warning"
    description: str
    impact_score: float  # 0.0 to 1.0
    confidence: float
    actionable: bool
    suggested_action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class LearningEngine:
    """
    Advanced learning system that continuously improves skill performance
    and adapts to user preferences and patterns.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('LearningEngine')
        
        # Learning configuration
        self.track_performance = config.get('track_performance', True)
        self.optimize_skills = config.get('optimize_skills', True)
        self.community_data = config.get('community_data', False)
        self.learning_rate = config.get('learning_rate', 0.1)
        self.min_samples_for_learning = config.get('min_samples_for_learning', 5)
        
        # Data storage
        self.db_path = config.get('db_path', 'miktos_learning.db')
        self._init_database()
        
        # In-memory caches
        self.skill_performance_cache: Dict[str, SkillPerformance] = {}
        self.user_preferences_cache: Dict[str, List[UserPreference]] = {}
        self.recent_insights: List[LearningInsight] = []
        
        # Learning patterns
        self.command_patterns: Dict[str, int] = {}
        self.error_patterns: Dict[str, int] = {}
        self.optimization_queue: List[str] = []
        
        # Performance baselines
        self.baseline_metrics = {
            'success_rate': 0.8,
            'execution_time': 2.0,
            'user_satisfaction': 0.7
        }
    
    def _init_database(self):
        """Initialize SQLite database for persistent learning data"""
        try:
            self.db_connection = sqlite3.connect(self.db_path)
            self.db_connection.row_factory = sqlite3.Row
            
            # Create tables
            cursor = self.db_connection.cursor()
            
            # Execution history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS execution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command_text TEXT NOT NULL,
                    primary_intent TEXT,
                    skills_used TEXT,  -- JSON array
                    success BOOLEAN,
                    execution_time REAL,
                    error_message TEXT,
                    parameters TEXT,  -- JSON object
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Skill performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skill_performance (
                    skill_name TEXT PRIMARY KEY,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    total_execution_time REAL DEFAULT 0.0,
                    parameter_data TEXT,  -- JSON object
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preference_type TEXT,
                    context TEXT,
                    preferred_value TEXT,
                    confidence REAL,
                    usage_count INTEGER DEFAULT 1,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Learning insights table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT,
                    description TEXT,
                    impact_score REAL,
                    confidence REAL,
                    actionable BOOLEAN,
                    suggested_action TEXT,
                    data TEXT,  -- JSON object
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.db_connection.commit()
            self.logger.info("Learning database initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize learning database: {e}")
            self.db_connection = None
    
    async def record_execution(self, command: AgentCommand, result: ExecutionResult):
        """Record command execution for learning analysis"""
        if not self.track_performance:
            return
        
        try:
            # Store in database
            if self.db_connection:
                cursor = self.db_connection.cursor()
                cursor.execute('''
                    INSERT INTO execution_history 
                    (command_text, primary_intent, skills_used, success, execution_time, error_message, parameters)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    command.text,
                    getattr(command, 'primary_intent', None),
                    json.dumps(result.skills_used or []),
                    result.success,
                    result.execution_time,
                    result.errors[0] if result.errors else None,
                    json.dumps(command.context)
                ))
                self.db_connection.commit()
            
            # Update skill performance
            if result.skills_used:
                for skill_name in result.skills_used:
                    await self._update_skill_performance(skill_name, result)
            
            # Analyze for patterns
            await self._analyze_execution_patterns(command, result)
            
            # Learn user preferences
            await self._learn_user_preferences(command, result)
            
            # Generate insights
            insights = await self._generate_insights(command, result)
            self.recent_insights.extend(insights)
            
            # Limit recent insights
            if len(self.recent_insights) > 100:
                self.recent_insights = self.recent_insights[-100:]
        
        except Exception as e:
            self.logger.error(f"Failed to record execution: {e}")
    
    async def _update_skill_performance(self, skill_name: str, result: ExecutionResult):
        """Update performance metrics for a skill"""
        try:
            # Get current performance from cache or database
            performance = self.skill_performance_cache.get(skill_name)
            
            if not performance:
                performance = await self._load_skill_performance(skill_name)
            
            # Update metrics
            if result.success:
                success_count = performance.usage_count * performance.success_rate
                performance.usage_count += 1
                performance.success_rate = (success_count + 1) / performance.usage_count
            else:
                performance.usage_count += 1
                success_count = performance.usage_count * performance.success_rate
                performance.success_rate = success_count / performance.usage_count
            
            # Update execution time (moving average)
            if result.execution_time:
                if performance.average_execution_time == 0:
                    performance.average_execution_time = result.execution_time
                else:
                    alpha = self.learning_rate
                    performance.average_execution_time = (
                        alpha * result.execution_time + 
                        (1 - alpha) * performance.average_execution_time
                    )
            
            # Update error patterns
            if result.errors:
                for error in result.errors:
                    if error not in performance.error_patterns:
                        performance.error_patterns.append(error)
            
            performance.last_updated = datetime.now()
            
            # Update cache and database
            self.skill_performance_cache[skill_name] = performance
            await self._save_skill_performance(performance)
        
        except Exception as e:
            self.logger.error(f"Failed to update skill performance for {skill_name}: {e}")
    
    async def _load_skill_performance(self, skill_name: str) -> SkillPerformance:
        """Load skill performance from database"""
        if self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute(
                'SELECT * FROM skill_performance WHERE skill_name = ?',
                (skill_name,)
            )
            row = cursor.fetchone()
            
            if row:
                parameter_data = json.loads(row['parameter_data']) if row['parameter_data'] else {}
                return SkillPerformance(
                    skill_name=skill_name,
                    success_rate=row['success_count'] / (row['success_count'] + row['failure_count']) if (row['success_count'] + row['failure_count']) > 0 else 0.0,
                    average_execution_time=row['total_execution_time'] / (row['success_count'] + row['failure_count']) if (row['success_count'] + row['failure_count']) > 0 else 0.0,
                    usage_count=row['success_count'] + row['failure_count'],
                    error_patterns=[],
                    parameter_effectiveness=parameter_data,
                    last_updated=datetime.fromisoformat(row['last_updated'])
                )
        
        # Return default performance for new skills
        return SkillPerformance(
            skill_name=skill_name,
            success_rate=0.0,
            average_execution_time=0.0,
            usage_count=0,
            error_patterns=[],
            parameter_effectiveness={},
            last_updated=datetime.now()
        )
    
    async def _save_skill_performance(self, performance: SkillPerformance):
        """Save skill performance to database"""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            success_count = int(performance.usage_count * performance.success_rate)
            failure_count = performance.usage_count - success_count
            total_execution_time = performance.average_execution_time * performance.usage_count
            
            cursor.execute('''
                INSERT OR REPLACE INTO skill_performance 
                (skill_name, success_count, failure_count, total_execution_time, parameter_data, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                performance.skill_name,
                success_count,
                failure_count,
                total_execution_time,
                json.dumps(performance.parameter_effectiveness),
                performance.last_updated.isoformat()
            ))
            
            self.db_connection.commit()
        
        except Exception as e:
            self.logger.error(f"Failed to save skill performance: {e}")
    
    async def _analyze_execution_patterns(self, command: AgentCommand, result: ExecutionResult):
        """Analyze execution patterns for learning opportunities"""
        try:
            # Track command patterns
            command_key = command.text.lower()[:50]  # First 50 chars as key
            self.command_patterns[command_key] = self.command_patterns.get(command_key, 0) + 1
            
            # Track error patterns
            if result.errors:
                for error in result.errors:
                    error_key = error[:100]  # First 100 chars as key
                    self.error_patterns[error_key] = self.error_patterns.get(error_key, 0) + 1
            
            # Identify optimization opportunities
            if result.execution_time and result.execution_time > 5.0:  # Slow execution
                skill_names = result.skills_used or []
                for skill_name in skill_names:
                    if skill_name not in self.optimization_queue:
                        self.optimization_queue.append(skill_name)
        
        except Exception as e:
            self.logger.error(f"Failed to analyze execution patterns: {e}")
    
    async def _learn_user_preferences(self, command: AgentCommand, result: ExecutionResult):
        """Learn user preferences from successful executions"""
        if not result.success:
            return
        
        try:
            # Extract potential preferences from command context
            context = command.context or {}
            
            # Learn parameter preferences
            for key, value in context.items():
                if isinstance(value, (int, float, str, bool)):
                    preference = UserPreference(
                        preference_type="parameter",
                        context=key,
                        preferred_value=value,
                        confidence=0.7,
                        usage_count=1,
                        last_seen=datetime.now()
                    )
                    
                    await self._update_user_preference(preference)
        
        except Exception as e:
            self.logger.error(f"Failed to learn user preferences: {e}")
    
    async def _update_user_preference(self, preference: UserPreference):
        """Update or create user preference"""
        try:
            # Check if preference exists in cache
            context_prefs = self.user_preferences_cache.get(preference.context, [])
            
            existing_pref = None
            for pref in context_prefs:
                if (pref.preference_type == preference.preference_type and 
                    pref.preferred_value == preference.preferred_value):
                    existing_pref = pref
                    break
            
            if existing_pref:
                # Update existing preference
                existing_pref.usage_count += 1
                existing_pref.confidence = min(existing_pref.confidence + 0.1, 1.0)
                existing_pref.last_seen = datetime.now()
            else:
                # Add new preference
                context_prefs.append(preference)
                self.user_preferences_cache[preference.context] = context_prefs
            
            # Save to database
            if self.db_connection:
                cursor = self.db_connection.cursor()
                if existing_pref:
                    cursor.execute('''
                        UPDATE user_preferences 
                        SET usage_count = ?, confidence = ?, last_seen = ?
                        WHERE preference_type = ? AND context = ? AND preferred_value = ?
                    ''', (
                        existing_pref.usage_count,
                        existing_pref.confidence,
                        existing_pref.last_seen.isoformat(),
                        preference.preference_type,
                        preference.context,
                        str(preference.preferred_value)
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO user_preferences 
                        (preference_type, context, preferred_value, confidence, usage_count, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        preference.preference_type,
                        preference.context,
                        str(preference.preferred_value),
                        preference.confidence,
                        preference.usage_count,
                        preference.last_seen.isoformat()
                    ))
                
                self.db_connection.commit()
        
        except Exception as e:
            self.logger.error(f"Failed to update user preference: {e}")
    
    async def _generate_insights(self, command: AgentCommand, result: ExecutionResult) -> List[LearningInsight]:
        """Generate learning insights from execution data"""
        insights = []
        
        try:
            # Performance insights
            if result.execution_time and result.execution_time > 10.0:
                insights.append(LearningInsight(
                    insight_type="optimization",
                    description=f"Slow execution detected: {result.execution_time:.2f}s",
                    impact_score=0.7,
                    confidence=0.9,
                    actionable=True,
                    suggested_action="Consider optimizing parameters or breaking into smaller operations"
                ))
            
            # Error pattern insights
            if result.errors:
                for error in result.errors:
                    if self.error_patterns.get(error[:100], 0) > 3:  # Repeated error
                        insights.append(LearningInsight(
                            insight_type="pattern",
                            description=f"Recurring error pattern: {error[:100]}",
                            impact_score=0.8,
                            confidence=0.8,
                            actionable=True,
                            suggested_action="Review and improve error handling for this pattern"
                        ))
            
            # Success pattern insights
            if result.success and result.skills_used:
                for skill_name in result.skills_used:
                    performance = self.skill_performance_cache.get(skill_name)
                    if performance and performance.success_rate > 0.95 and performance.usage_count > 10:
                        insights.append(LearningInsight(
                            insight_type="optimization",
                            description=f"Skill '{skill_name}' has excellent performance",
                            impact_score=0.6,
                            confidence=0.9,
                            actionable=True,
                            suggested_action="Consider using this skill as a template for similar operations"
                        ))
            
            # Store insights in database
            if insights and self.db_connection:
                cursor = self.db_connection.cursor()
                for insight in insights:
                    cursor.execute('''
                        INSERT INTO learning_insights 
                        (insight_type, description, impact_score, confidence, actionable, suggested_action, data)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        insight.insight_type,
                        insight.description,
                        insight.impact_score,
                        insight.confidence,
                        insight.actionable,
                        insight.suggested_action,
                        json.dumps(insight.data) if insight.data else None
                    ))
                
                self.db_connection.commit()
        
        except Exception as e:
            self.logger.error(f"Failed to generate insights: {e}")
        
        return insights
    
    async def optimize_skills(self):
        """Optimize skills based on performance data"""
        if not self.optimize_skills:
            return
        
        try:
            optimized_count = 0
            
            # Process optimization queue
            for skill_name in self.optimization_queue[:10]:  # Limit to 10 per run
                performance = self.skill_performance_cache.get(skill_name)
                if not performance:
                    performance = await self._load_skill_performance(skill_name)
                
                if performance.usage_count >= self.min_samples_for_learning:
                    await self._optimize_skill(skill_name, performance)
                    optimized_count += 1
            
            # Clear processed items from queue
            self.optimization_queue = self.optimization_queue[10:]
            
            self.logger.info(f"Optimized {optimized_count} skills")
        
        except Exception as e:
            self.logger.error(f"Failed to optimize skills: {e}")
    
    async def _optimize_skill(self, skill_name: str, performance: SkillPerformance):
        """Optimize a specific skill based on performance data"""
        try:
            optimizations = []
            
            # Check success rate
            if performance.success_rate < self.baseline_metrics['success_rate']:
                optimizations.append(f"Improve success rate (current: {performance.success_rate:.2f})")
            
            # Check execution time
            if performance.average_execution_time > self.baseline_metrics['execution_time']:
                optimizations.append(f"Reduce execution time (current: {performance.average_execution_time:.2f}s)")
            
            # Analyze error patterns
            if performance.error_patterns:
                most_common_error = max(set(performance.error_patterns), key=performance.error_patterns.count)
                optimizations.append(f"Address common error: {most_common_error}")
            
            if optimizations:
                insight = LearningInsight(
                    insight_type="optimization",
                    description=f"Optimization opportunities for {skill_name}",
                    impact_score=0.8,
                    confidence=0.7,
                    actionable=True,
                    suggested_action="; ".join(optimizations),
                    data={"skill_name": skill_name, "performance": asdict(performance)}
                )
                
                self.recent_insights.append(insight)
                self.logger.info(f"Generated optimization plan for {skill_name}")
        
        except Exception as e:
            self.logger.error(f"Failed to optimize skill {skill_name}: {e}")
    
    async def get_skill_recommendations(self, command_context: Dict[str, Any]) -> List[str]:
        """Get skill recommendations based on learning data"""
        recommendations = []
        
        try:
            # Analyze command context for patterns
            for skill_name, performance in self.skill_performance_cache.items():
                if performance.success_rate > 0.8 and performance.usage_count > 5:
                    # Check if skill parameters match context
                    for param, effectiveness in performance.parameter_effectiveness.items():
                        if param in command_context and effectiveness > 0.7:
                            recommendations.append(skill_name)
                            break
            
            # Sort by success rate
            recommendations.sort(key=lambda x: self.skill_performance_cache[x].success_rate, reverse=True)
            
            return recommendations[:5]  # Return top 5
        
        except Exception as e:
            self.logger.error(f"Failed to get skill recommendations: {e}")
            return []
    
    async def get_parameter_suggestions(self, skill_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get parameter suggestions based on learned preferences"""
        suggestions = {}
        
        try:
            # Get skill performance data
            performance = self.skill_performance_cache.get(skill_name)
            if performance:
                suggestions.update(performance.parameter_effectiveness)
            
            # Add user preferences
            for context_key, prefs in self.user_preferences_cache.items():
                if context_key in context:
                    for pref in prefs:
                        if pref.confidence > 0.7:
                            suggestions[pref.context] = pref.preferred_value
            
            return suggestions
        
        except Exception as e:
            self.logger.error(f"Failed to get parameter suggestions: {e}")
            return {}
    
    def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning engine status"""
        return {
            "tracking_enabled": self.track_performance,
            "optimization_enabled": self.optimize_skills,
            "skills_tracked": len(self.skill_performance_cache),
            "user_preferences": sum(len(prefs) for prefs in self.user_preferences_cache.values()),
            "recent_insights": len(self.recent_insights),
            "optimization_queue": len(self.optimization_queue),
            "database_connected": self.db_connection is not None
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all skills"""
        if not self.skill_performance_cache:
            return {"message": "No performance data available"}
        
        total_usage = sum(p.usage_count for p in self.skill_performance_cache.values())
        avg_success_rate = sum(p.success_rate * p.usage_count for p in self.skill_performance_cache.values()) / total_usage if total_usage > 0 else 0
        avg_execution_time = sum(p.average_execution_time * p.usage_count for p in self.skill_performance_cache.values()) / total_usage if total_usage > 0 else 0
        
        return {
            "total_skills": len(self.skill_performance_cache),
            "total_executions": total_usage,
            "average_success_rate": avg_success_rate,
            "average_execution_time": avg_execution_time,
            "top_performing_skills": sorted(
                self.skill_performance_cache.keys(),
                key=lambda x: self.skill_performance_cache[x].success_rate,
                reverse=True
            )[:5]
        }
    
    def export_learning_data(self) -> Dict[str, Any]:
        """Export learning data for analysis or backup"""
        return {
            "skill_performance": {name: asdict(perf) for name, perf in self.skill_performance_cache.items()},
            "user_preferences": {context: [asdict(pref) for pref in prefs] for context, prefs in self.user_preferences_cache.items()},
            "recent_insights": [asdict(insight) for insight in self.recent_insights],
            "command_patterns": self.command_patterns,
            "error_patterns": self.error_patterns,
            "export_timestamp": datetime.now().isoformat()
        }
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old learning data"""
        if not self.db_connection:
            return
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            cursor = self.db_connection.cursor()
            
            # Clean old execution history
            cursor.execute('DELETE FROM execution_history WHERE timestamp < ?', (cutoff_date,))
            
            # Clean old insights
            cursor.execute('DELETE FROM learning_insights WHERE created_at < ?', (cutoff_date,))
            
            # Clean old preferences that haven't been used
            cursor.execute('DELETE FROM user_preferences WHERE last_seen < ? AND usage_count < 3', (cutoff_date,))
            
            self.db_connection.commit()
            self.logger.info(f"Cleaned up learning data older than {days_to_keep} days")
        
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
    
    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'db_connection') and self.db_connection:
            self.db_connection.close()


if __name__ == "__main__":
    # Test the learning engine
    print("Learning engine module loaded successfully")
