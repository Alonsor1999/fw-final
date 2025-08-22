"""
LoadBalancer MVP - Balanceador inteligente para optimal routing
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from framework.models.module import Module, ModuleHealth

logger = logging.getLogger(__name__)


class LoadBalancerMVP:
    """Balanceador inteligente que optimiza robot distribution basado en real-time metrics"""
    
    def __init__(self):
        self.module_cache: Dict[str, Module] = {}
        self.performance_cache: Dict[str, float] = {}
        self.last_selection_time: Dict[str, datetime] = {}

    def select_best_module(self, modules: List[Module]) -> Module:
        """Seleccionar mejor módulo usando weighted scoring"""
        if not modules:
            raise ValueError("No modules available for selection")
        
        if len(modules) == 1:
            return modules[0]
        
        best_score = 0.0
        best_module = None
        
        for module in modules:
            # Calculate weighted score: performance (50%) + capacity (30%) + health (20%)
            performance_score = module.performance_score
            capacity_score = 1.0 - module.capacity_utilization  # Inverse of utilization
            health_score = 1.0 if module.is_healthy() else 0.0
            
            overall_score = (
                performance_score * 0.5 +
                capacity_score * 0.3 +
                health_score * 0.2
            )
            
            # Apply additional factors
            overall_score = self._apply_additional_factors(module, overall_score)
            
            if overall_score > best_score:
                best_score = overall_score
                best_module = module
        
        if best_module:
            # Update selection tracking
            self.last_selection_time[best_module.module_name] = datetime.utcnow()
            logger.debug(f"Selected module {best_module.module_name} with score {best_score:.3f}")
        
        return best_module or modules[0]

    def _apply_additional_factors(self, module: Module, base_score: float) -> float:
        """Aplicar factores adicionales al score"""
        adjusted_score = base_score
        
        # Factor 1: Recent selection penalty (avoid overloading same module)
        if module.module_name in self.last_selection_time:
            time_since_last = (datetime.utcnow() - self.last_selection_time[module.module_name]).total_seconds()
            if time_since_last < 60:  # Within last minute
                adjusted_score *= 0.8  # 20% penalty
        
        # Factor 2: Error rate penalty
        if module.error_count_24h > 0:
            error_penalty = min(module.error_count_24h / 100.0, 0.3)  # Max 30% penalty
            adjusted_score *= (1.0 - error_penalty)
        
        # Factor 3: Consecutive failures penalty
        if module.consecutive_failures > 0:
            failure_penalty = min(module.consecutive_failures / 10.0, 0.5)  # Max 50% penalty
            adjusted_score *= (1.0 - failure_penalty)
        
        # Factor 4: Processing time penalty (prefer faster modules)
        if module.avg_processing_time_ms > 0:
            time_penalty = min(module.avg_processing_time_ms / 10000.0, 0.2)  # Max 20% penalty
            adjusted_score *= (1.0 - time_penalty)
        
        return adjusted_score

    def get_module_capacity(self, module: Module) -> float:
        """Obtener capacidad disponible del módulo"""
        # Base capacity
        base_capacity = 1.0 - module.capacity_utilization
        
        # Adjust based on health status
        if not module.is_healthy():
            base_capacity *= 0.5
        
        # Adjust based on error rate
        if module.error_count_24h > 10:
            base_capacity *= 0.7
        
        return max(0.0, base_capacity)

    def can_handle_robot_type(self, module: Module, robot_type: str) -> bool:
        """Verificar si módulo puede manejar tipo de robot"""
        return module.can_process_robot_type(robot_type)

    def get_optimal_modules_for_type(self, modules: List[Module], robot_type: str) -> List[Module]:
        """Obtener módulos óptimos para tipo de robot específico"""
        # Filter by robot type support
        supported_modules = [
            module for module in modules 
            if self.can_handle_robot_type(module, robot_type)
        ]
        
        # Sort by overall score
        scored_modules = []
        for module in supported_modules:
            score = (
                module.performance_score * 0.5 +
                (1.0 - module.capacity_utilization) * 0.3 +
                (1.0 if module.is_healthy() else 0.0) * 0.2
            )
            scored_modules.append((module, score))
        
        # Sort by score (descending)
        scored_modules.sort(key=lambda x: x[1], reverse=True)
        
        return [module for module, score in scored_modules]

    def update_module_performance(self, module_name: str, performance_data: Dict[str, Any]):
        """Actualizar datos de performance del módulo"""
        if module_name in self.module_cache:
            module = self.module_cache[module_name]
            
            # Update performance score
            if 'performance_score' in performance_data:
                module.performance_score = performance_data['performance_score']
            
            # Update capacity utilization
            if 'capacity_utilization' in performance_data:
                module.capacity_utilization = performance_data['capacity_utilization']
            
            # Update error count
            if 'error_count_24h' in performance_data:
                module.error_count_24h = performance_data['error_count_24h']
            
            # Update consecutive failures
            if 'consecutive_failures' in performance_data:
                module.consecutive_failures = performance_data['consecutive_failures']
            
            # Update processing time
            if 'avg_processing_time_ms' in performance_data:
                module.avg_processing_time_ms = performance_data['avg_processing_time_ms']
            
            logger.debug(f"Updated performance for module {module_name}")

    def get_load_distribution(self, modules: List[Module]) -> Dict[str, float]:
        """Obtener distribución de carga actual"""
        distribution = {}
        total_capacity = 0.0
        
        for module in modules:
            capacity = self.get_module_capacity(module)
            distribution[module.module_name] = capacity
            total_capacity += capacity
        
        # Normalize to percentages
        if total_capacity > 0:
            for module_name in distribution:
                distribution[module_name] = (distribution[module_name] / total_capacity) * 100
        
        return distribution

    def get_bottleneck_modules(self, modules: List[Module]) -> List[Module]:
        """Identificar módulos que son bottlenecks"""
        bottlenecks = []
        
        for module in modules:
            # Check for high utilization
            if module.capacity_utilization > 0.8:
                bottlenecks.append(module)
                continue
            
            # Check for high error rate
            if module.error_count_24h > 20:
                bottlenecks.append(module)
                continue
            
            # Check for consecutive failures
            if module.consecutive_failures > 5:
                bottlenecks.append(module)
                continue
            
            # Check for poor performance
            if module.performance_score < 0.5:
                bottlenecks.append(module)
                continue
        
        return bottlenecks

    def get_recommended_scaling(self, modules: List[Module]) -> Dict[str, str]:
        """Obtener recomendaciones de scaling"""
        recommendations = {}
        
        for module in modules:
            if module.capacity_utilization > 0.9:
                recommendations[module.module_name] = "CRITICAL_SCALE_UP"
            elif module.capacity_utilization > 0.7:
                recommendations[module.module_name] = "SCALE_UP"
            elif module.capacity_utilization < 0.2:
                recommendations[module.module_name] = "SCALE_DOWN"
            elif module.error_count_24h > 50:
                recommendations[module.module_name] = "INVESTIGATE_ERRORS"
            elif module.consecutive_failures > 10:
                recommendations[module.module_name] = "RESTART_MODULE"
            else:
                recommendations[module.module_name] = "STABLE"
        
        return recommendations

    def get_performance_summary(self, modules: List[Module]) -> Dict[str, Any]:
        """Obtener resumen de performance de todos los módulos"""
        if not modules:
            return {}
        
        total_modules = len(modules)
        healthy_modules = len([m for m in modules if m.is_healthy()])
        high_performance_modules = len([m for m in modules if m.performance_score > 0.8])
        
        avg_performance = sum(m.performance_score for m in modules) / total_modules
        avg_capacity_utilization = sum(m.capacity_utilization for m in modules) / total_modules
        total_errors = sum(m.error_count_24h for m in modules)
        
        return {
            "total_modules": total_modules,
            "healthy_modules": healthy_modules,
            "health_percentage": (healthy_modules / total_modules) * 100,
            "high_performance_modules": high_performance_modules,
            "avg_performance_score": avg_performance,
            "avg_capacity_utilization": avg_capacity_utilization,
            "total_errors_24h": total_errors,
            "bottleneck_count": len(self.get_bottleneck_modules(modules)),
            "load_distribution": self.get_load_distribution(modules),
            "scaling_recommendations": self.get_recommended_scaling(modules)
        }

    def reset_selection_history(self):
        """Resetear historial de selecciones"""
        self.last_selection_time.clear()
        logger.info("Load balancer selection history reset")

    def get_selection_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de selección"""
        now = datetime.utcnow()
        recent_selections = {}
        
        for module_name, last_time in self.last_selection_time.items():
            time_diff = (now - last_time).total_seconds()
            if time_diff < 3600:  # Last hour
                recent_selections[module_name] = time_diff
        
        return {
            "total_selections_tracked": len(self.last_selection_time),
            "recent_selections": recent_selections,
            "most_recently_selected": min(self.last_selection_time.items(), key=lambda x: x[1])[0] if self.last_selection_time else None
        }
