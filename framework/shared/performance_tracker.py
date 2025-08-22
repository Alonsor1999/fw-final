"""
PerformanceTracker MVP - Sistema de tracking de performance en tiempo real
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class PerformanceTrackerMVP:
    """Sistema de tracking de performance con métricas en tiempo real"""
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        
        # Operation tracking
        self.operation_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.operation_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        
        # System metrics
        self.system_metrics: Dict[str, Any] = {}
        self.system_history: deque = deque(maxlen=max_history_size)
        
        # Performance targets
        self.performance_targets = {
            "robot_creation": 50,      # ms
            "status_update": 25,       # ms
            "module_selection": 15,    # ms
            "progress_tracking": 10,   # ms
            "health_check": 10,        # ms
            "database_query": 25,      # ms
            "cache_operation": 5       # ms
        }

    async def record_operation(self, operation_type: str, duration_ms: float, 
                             status: str = "success", error_message: Optional[str] = None):
        """Registrar métrica de operación"""
        timestamp = datetime.utcnow()
        
        # Create operation record
        operation_record = {
            "timestamp": timestamp,
            "operation_type": operation_type,
            "duration_ms": duration_ms,
            "status": status,
            "error_message": error_message,
            "target_ms": self.performance_targets.get(operation_type, 100)
        }
        
        # Update operation metrics
        if operation_type not in self.operation_metrics:
            self.operation_metrics[operation_type] = {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": float('inf'),
                "max_duration_ms": 0,
                "target_compliance_rate": 0,
                "last_operation": None
            }
        
        metrics = self.operation_metrics[operation_type]
        
        # Update counters
        metrics["total_operations"] += 1
        metrics["total_duration_ms"] += duration_ms
        
        if status == "success":
            metrics["successful_operations"] += 1
        else:
            metrics["failed_operations"] += 1
        
        # Update duration statistics
        metrics["avg_duration_ms"] = metrics["total_duration_ms"] / metrics["total_operations"]
        metrics["min_duration_ms"] = min(metrics["min_duration_ms"], duration_ms)
        metrics["max_duration_ms"] = max(metrics["max_duration_ms"], duration_ms)
        
        # Calculate target compliance
        target_ms = self.performance_targets.get(operation_type, 100)
        if duration_ms <= target_ms:
            compliance_count = sum(1 for record in self.operation_history[operation_type] 
                                 if record["duration_ms"] <= target_ms)
            metrics["target_compliance_rate"] = (compliance_count + 1) / metrics["total_operations"]
        else:
            compliance_count = sum(1 for record in self.operation_history[operation_type] 
                                 if record["duration_ms"] <= target_ms)
            metrics["target_compliance_rate"] = compliance_count / metrics["total_operations"]
        
        metrics["last_operation"] = timestamp
        
        # Add to history
        self.operation_history[operation_type].append(operation_record)
        
        # Log performance issues
        if duration_ms > target_ms * 2:  # 2x target
            logger.warning(f"Performance issue: {operation_type} took {duration_ms:.2f}ms (target: {target_ms}ms)")
        
        if status == "error":
            logger.error(f"Operation failed: {operation_type} - {error_message}")

    async def record_system_metric(self, metric_name: str, value: float, unit: str = ""):
        """Registrar métrica del sistema"""
        timestamp = datetime.utcnow()
        
        system_record = {
            "timestamp": timestamp,
            "metric_name": metric_name,
            "value": value,
            "unit": unit
        }
        
        self.system_metrics[metric_name] = {
            "current_value": value,
            "unit": unit,
            "last_updated": timestamp
        }
        
        self.system_history.append(system_record)

    async def get_operation_metrics(self, operation_type: Optional[str] = None, 
                                  time_range_minutes: int = 60) -> Dict[str, Any]:
        """Obtener métricas de operaciones"""
        if operation_type:
            return self._get_single_operation_metrics(operation_type, time_range_minutes)
        else:
            return self._get_all_operation_metrics(time_range_minutes)

    def _get_single_operation_metrics(self, operation_type: str, time_range_minutes: int) -> Dict[str, Any]:
        """Obtener métricas de una operación específica"""
        if operation_type not in self.operation_metrics:
            return {}
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_range_minutes)
        
        # Filter recent operations
        recent_operations = [
            record for record in self.operation_history[operation_type]
            if record["timestamp"] >= cutoff_time
        ]
        
        if not recent_operations:
            return {}
        
        # Calculate metrics for time range
        durations = [op["duration_ms"] for op in recent_operations]
        successful = [op for op in recent_operations if op["status"] == "success"]
        failed = [op for op in recent_operations if op["status"] == "error"]
        
        target_ms = self.performance_targets.get(operation_type, 100)
        within_target = [op for op in recent_operations if op["duration_ms"] <= target_ms]
        
        return {
            "operation_type": operation_type,
            "time_range_minutes": time_range_minutes,
            "total_operations": len(recent_operations),
            "successful_operations": len(successful),
            "failed_operations": len(failed),
            "success_rate": len(successful) / len(recent_operations) if recent_operations else 0,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "target_compliance_rate": len(within_target) / len(recent_operations) if recent_operations else 0,
            "target_ms": target_ms,
            "last_operation": recent_operations[-1]["timestamp"] if recent_operations else None
        }

    def _get_all_operation_metrics(self, time_range_minutes: int) -> Dict[str, Any]:
        """Obtener métricas de todas las operaciones"""
        all_metrics = {}
        
        for operation_type in self.operation_metrics.keys():
            all_metrics[operation_type] = self._get_single_operation_metrics(operation_type, time_range_minutes)
        
        # Calculate overall metrics
        total_operations = sum(metrics.get("total_operations", 0) for metrics in all_metrics.values())
        total_successful = sum(metrics.get("successful_operations", 0) for metrics in all_metrics.values())
        total_failed = sum(metrics.get("failed_operations", 0) for metrics in all_metrics.values())
        
        overall_success_rate = total_successful / total_operations if total_operations > 0 else 0
        
        return {
            "overall": {
                "total_operations": total_operations,
                "successful_operations": total_successful,
                "failed_operations": total_failed,
                "success_rate": overall_success_rate,
                "time_range_minutes": time_range_minutes
            },
            "operations": all_metrics
        }

    async def get_system_metrics(self, time_range_minutes: int = 60) -> Dict[str, Any]:
        """Obtener métricas del sistema"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_range_minutes)
        
        # Filter recent system metrics
        recent_metrics = [
            record for record in self.system_history
            if record["timestamp"] >= cutoff_time
        ]
        
        # Group by metric name
        metrics_by_name = defaultdict(list)
        for record in recent_metrics:
            metrics_by_name[record["metric_name"]].append(record)
        
        # Calculate statistics for each metric
        system_metrics = {}
        for metric_name, records in metrics_by_name.items():
            values = [record["value"] for record in records]
            unit = records[0]["unit"] if records else ""
            
            system_metrics[metric_name] = {
                "current_value": values[-1] if values else 0,
                "avg_value": sum(values) / len(values) if values else 0,
                "min_value": min(values) if values else 0,
                "max_value": max(values) if values else 0,
                "unit": unit,
                "data_points": len(values),
                "last_updated": records[-1]["timestamp"] if records else None
            }
        
        return system_metrics

    async def get_performance_alerts(self, time_range_minutes: int = 15) -> List[Dict[str, Any]]:
        """Obtener alertas de performance"""
        alerts = []
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_range_minutes)
        
        for operation_type in self.operation_metrics.keys():
            # Get recent operations
            recent_operations = [
                record for record in self.operation_history[operation_type]
                if record["timestamp"] >= cutoff_time
            ]
            
            if not recent_operations:
                continue
            
            target_ms = self.performance_targets.get(operation_type, 100)
            
            # Check for performance issues
            slow_operations = [op for op in recent_operations if op["duration_ms"] > target_ms * 1.5]
            failed_operations = [op for op in recent_operations if op["status"] == "error"]
            
            if slow_operations:
                avg_slow_duration = sum(op["duration_ms"] for op in slow_operations) / len(slow_operations)
                alerts.append({
                    "type": "PERFORMANCE_DEGRADATION",
                    "operation_type": operation_type,
                    "severity": "WARNING",
                    "message": f"{operation_type} is running slow: {avg_slow_duration:.2f}ms avg (target: {target_ms}ms)",
                    "affected_operations": len(slow_operations),
                    "timestamp": datetime.utcnow()
                })
            
            if failed_operations:
                failure_rate = len(failed_operations) / len(recent_operations)
                if failure_rate > 0.1:  # More than 10% failure rate
                    alerts.append({
                        "type": "HIGH_FAILURE_RATE",
                        "operation_type": operation_type,
                        "severity": "ERROR",
                        "message": f"{operation_type} has high failure rate: {failure_rate:.1%}",
                        "failed_operations": len(failed_operations),
                        "total_operations": len(recent_operations),
                        "timestamp": datetime.utcnow()
                    })
        
        return alerts

    async def get_performance_summary(self, time_range_minutes: int = 60) -> Dict[str, Any]:
        """Obtener resumen de performance"""
        operation_metrics = await self.get_operation_metrics(time_range_minutes=time_range_minutes)
        system_metrics = await self.get_system_metrics(time_range_minutes=time_range_minutes)
        alerts = await self.get_performance_alerts(time_range_minutes=time_range_minutes)
        
        # Calculate overall performance score
        overall_score = self._calculate_performance_score(operation_metrics)
        
        return {
            "timestamp": datetime.utcnow(),
            "time_range_minutes": time_range_minutes,
            "overall_performance_score": overall_score,
            "performance_level": self._get_performance_level(overall_score),
            "operation_metrics": operation_metrics,
            "system_metrics": system_metrics,
            "alerts": alerts,
            "targets": self.performance_targets
        }

    def _calculate_performance_score(self, operation_metrics: Dict[str, Any]) -> float:
        """Calcular score general de performance"""
        if "operations" not in operation_metrics:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for operation_type, metrics in operation_metrics["operations"].items():
            if not metrics:
                continue
            
            # Weight based on operation frequency
            weight = metrics.get("total_operations", 0)
            total_weight += weight
            
            # Calculate operation score
            success_rate = metrics.get("success_rate", 0)
            target_compliance = metrics.get("target_compliance_rate", 0)
            
            operation_score = (success_rate * 0.6) + (target_compliance * 0.4)
            total_score += operation_score * weight
        
        return total_score / total_weight if total_weight > 0 else 0.0

    def _get_performance_level(self, score: float) -> str:
        """Obtener nivel de performance basado en score"""
        if score >= 0.95:
            return "EXCELLENT"
        elif score >= 0.85:
            return "GOOD"
        elif score >= 0.70:
            return "ACCEPTABLE"
        elif score >= 0.50:
            return "POOR"
        else:
            return "CRITICAL"

    async def reset_metrics(self):
        """Resetear todas las métricas"""
        self.operation_metrics.clear()
        self.operation_history.clear()
        self.system_metrics.clear()
        self.system_history.clear()
        logger.info("Performance metrics reset")

    async def get_metrics_history(self, operation_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener historial de métricas de una operación"""
        if operation_type not in self.operation_history:
            return []
        
        return list(self.operation_history[operation_type])[-limit:]

    async def export_metrics(self, format: str = "json") -> Dict[str, Any]:
        """Exportar métricas en formato específico"""
        if format.lower() == "json":
            return {
                "operation_metrics": dict(self.operation_metrics),
                "system_metrics": self.system_metrics,
                "performance_targets": self.performance_targets,
                "export_timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def set_performance_target(self, operation_type: str, target_ms: float):
        """Establecer target de performance para operación"""
        self.performance_targets[operation_type] = target_ms
        logger.info(f"Set performance target for {operation_type}: {target_ms}ms")

    def get_performance_targets(self) -> Dict[str, float]:
        """Obtener todos los targets de performance"""
        return self.performance_targets.copy()
