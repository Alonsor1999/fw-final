"""
SecurityValidator MVP - Sistema de autenticación y validación
"""
import hashlib
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

from framework.config import settings, SECURITY_CONFIG
from framework.models.robot import RobotCreate

logger = logging.getLogger(__name__)


class RateLimiterMVP:
    """Rate limiter simplificado con Redis-like counters"""
    
    def __init__(self):
        self.counters: Dict[str, Dict[str, Any]] = {}
        self.limits = {
            "default": {"requests": 100, "window": 60},  # 100 requests per minute
            "health_check": {"requests": 1000, "window": 60},  # 1000 requests per minute
            "bulk_operations": {"requests": 10, "window": 60}  # 10 requests per minute
        }

    def check_limit(self, key: str, limit_type: str = "default") -> bool:
        """Verificar si request está dentro del límite"""
        now = time.time()
        limit_config = self.limits.get(limit_type, self.limits["default"])
        
        if key not in self.counters:
            self.counters[key] = {
                "count": 0,
                "window_start": now
            }
        
        counter = self.counters[key]
        
        # Reset window if expired
        if now - counter["window_start"] > limit_config["window"]:
            counter["count"] = 0
            counter["window_start"] = now
        
        # Check limit
        if counter["count"] >= limit_config["requests"]:
            return False
        
        # Increment counter
        counter["count"] += 1
        return True

    def get_remaining_requests(self, key: str, limit_type: str = "default") -> int:
        """Obtener requests restantes"""
        now = time.time()
        limit_config = self.limits.get(limit_type, self.limits["default"])
        
        if key not in self.counters:
            return limit_config["requests"]
        
        counter = self.counters[key]
        
        # Reset window if expired
        if now - counter["window_start"] > limit_config["window"]:
            return limit_config["requests"]
        
        return max(0, limit_config["requests"] - counter["count"])


class SecurityValidatorMVP:
    """Sistema de autenticación centralizado con API keys y rate limiting"""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.rate_limiter = RateLimiterMVP()
        self.audit_log: List[Dict[str, Any]] = []
        
        # Initialize with some test API keys
        self._initialize_test_keys()

    def _initialize_test_keys(self):
        """Inicializar con API keys de prueba"""
        test_keys = {
            "test_key_legal": {
                "module_name": "LegalModule",
                "permissions": ["legal_document_analysis", "contract_review"],
                "created_at": datetime.utcnow(),
                "last_used": None
            },
            "test_key_email": {
                "module_name": "EmailProcessor", 
                "permissions": ["email_classification", "spam_detection"],
                "created_at": datetime.utcnow(),
                "last_used": None
            },
            "test_key_ocr": {
                "module_name": "OCREngine",
                "permissions": ["document_ocr", "image_processing"],
                "created_at": datetime.utcnow(),
                "last_used": None
            },
            "test_key_scraping": {
                "module_name": "ScrapingModule",
                "permissions": ["WebScraper", "web_automation", "web_scraping", "scraping"],
                "created_at": datetime.utcnow(),
                "last_used": None
            }
        }
        
        for key, data in test_keys.items():
            key_hash = self._hash_api_key(key)
            self.api_keys[key_hash] = data

    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key usando SHA-256"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def validate_request(self, robot_data: RobotCreate, api_key: str) -> str:
        """Validar request completo con authentication y rate limiting"""
        start_time = time.time()
        
        try:
            # 1. API Key validation (2-3ms)
            module_name = await self._validate_api_key(api_key)
            
            # 2. Rate limiting check (1-2ms)
            await self._check_rate_limit(api_key, robot_data.robot_type)
            
            # 3. Input validation (2-5ms)
            await self._validate_input_data(robot_data)
            
            # 4. Permission check
            await self._check_permissions(api_key, robot_data.robot_type)
            
            # 5. Audit logging (async, no latency)
            asyncio.create_task(self._log_access(module_name, robot_data, api_key))
            
            # Update last used timestamp
            key_hash = self._hash_api_key(api_key)
            if key_hash in self.api_keys:
                self.api_keys[key_hash]["last_used"] = datetime.utcnow()
            
            validation_time = (time.time() - start_time) * 1000
            logger.debug(f"Request validated in {validation_time:.2f}ms for module: {module_name}")
            
            return module_name
            
        except Exception as e:
            validation_time = (time.time() - start_time) * 1000
            logger.error(f"Request validation failed in {validation_time:.2f}ms: {e}")
            raise

    async def _validate_api_key(self, api_key: str) -> str:
        """Validar API key y obtener module name"""
        if not api_key:
            raise ValueError("API key is required")
        
        key_hash = self._hash_api_key(api_key)
        
        if key_hash not in self.api_keys:
            raise ValueError("Invalid API key")
        
        key_data = self.api_keys[key_hash]
        
        # Check if key is expired (optional feature)
        if "expires_at" in key_data and key_data["expires_at"]:
            if datetime.utcnow() > key_data["expires_at"]:
                raise ValueError("API key has expired")
        
        return key_data["module_name"]

    async def _check_rate_limit(self, api_key: str, robot_type: str):
        """Verificar rate limiting"""
        # Use API key as rate limit key
        if not self.rate_limiter.check_limit(api_key, "default"):
            remaining = self.rate_limiter.get_remaining_requests(api_key, "default")
            raise ValueError(f"Rate limit exceeded. Try again later. Remaining requests: {remaining}")

    async def _validate_input_data(self, robot_data: RobotCreate):
        """Validar datos de entrada"""
        # Validate robot type
        if not robot_data.robot_type or len(robot_data.robot_type) > 50:
            raise ValueError("Invalid robot type")
        
        # Validate config data (replaces input_data)
        if not robot_data.config_data:
            raise ValueError("Config data is required")
        
        # Check for potentially malicious content
        await self._sanitize_input(robot_data.config_data)

    async def _sanitize_input(self, input_data: Dict[str, Any]):
        """Sanitizar datos de entrada"""
        # Check for SQL injection patterns
        sql_patterns = ["'", "DROP", "DELETE", "INSERT", "UPDATE", "SELECT", "UNION"]
        input_str = str(input_data).upper()
        
        for pattern in sql_patterns:
            if pattern in input_str:
                logger.warning(f"Potential SQL injection detected: {pattern}")
                # For MVP, we'll just log the warning
                # In production, this would raise an exception
        
        # Check for XSS patterns
        xss_patterns = ["<script>", "javascript:", "onload=", "onerror="]
        for pattern in xss_patterns:
            if pattern.lower() in input_str.lower():
                logger.warning(f"Potential XSS detected: {pattern}")
                # For MVP, we'll just log the warning

    async def _check_permissions(self, api_key: str, robot_type: str):
        """Verificar permisos para robot type"""
        key_hash = self._hash_api_key(api_key)
        key_data = self.api_keys[key_hash]
        
        if "permissions" not in key_data:
            raise ValueError("No permissions defined for API key")
        
        if robot_type not in key_data["permissions"]:
            raise ValueError(f"API key does not have permission for robot type: {robot_type}")

    async def _log_access(self, module_name: str, robot_data: RobotCreate, api_key: str):
        """Log access para audit trail"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "module_name": module_name,
            "robot_type": robot_data.robot_type,
            "api_key_hash": self._hash_api_key(api_key)[:8] + "...",  # Partial hash for privacy
            "robot_name": robot_data.robot_name,
            "success": True
        }
        
        self.audit_log.append(audit_entry)
        
        # Keep only last 1000 entries for MVP
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]

    def create_api_key(self, module_name: str, permissions: List[str], 
                      expires_at: Optional[datetime] = None) -> str:
        """Crear nueva API key"""
        import secrets
        
        # Generate random API key
        api_key = secrets.token_urlsafe(32)
        
        # Store key data
        key_hash = self._hash_api_key(api_key)
        self.api_keys[key_hash] = {
            "module_name": module_name,
            "permissions": permissions,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "last_used": None
        }
        
        logger.info(f"Created API key for module: {module_name}")
        return api_key

    def revoke_api_key(self, api_key: str) -> bool:
        """Revocar API key"""
        key_hash = self._hash_api_key(api_key)
        
        if key_hash in self.api_keys:
            del self.api_keys[key_hash]
            logger.info(f"Revoked API key: {key_hash[:8]}...")
            return True
        
        return False

    def get_api_key_info(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Obtener información de API key"""
        key_hash = self._hash_api_key(api_key)
        
        if key_hash in self.api_keys:
            key_data = self.api_keys[key_hash].copy()
            # Don't return sensitive information
            key_data["key_hash"] = key_hash[:8] + "..."
            return key_data
        
        return None

    def get_rate_limit_info(self, api_key: str) -> Dict[str, Any]:
        """Obtener información de rate limiting"""
        return {
            "default": {
                "remaining": self.rate_limiter.get_remaining_requests(api_key, "default"),
                "limit": self.rate_limiter.limits["default"]["requests"],
                "window": self.rate_limiter.limits["default"]["window"]
            },
            "health_check": {
                "remaining": self.rate_limiter.get_remaining_requests(api_key, "health_check"),
                "limit": self.rate_limiter.limits["health_check"]["requests"],
                "window": self.rate_limiter.limits["health_check"]["window"]
            },
            "bulk_operations": {
                "remaining": self.rate_limiter.get_remaining_requests(api_key, "bulk_operations"),
                "limit": self.rate_limiter.limits["bulk_operations"]["requests"],
                "window": self.rate_limiter.limits["bulk_operations"]["window"]
            }
        }

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener audit log"""
        return self.audit_log[-limit:]

    def get_security_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de seguridad"""
        now = datetime.utcnow()
        
        # Count active API keys
        active_keys = len(self.api_keys)
        
        # Count recent access attempts
        recent_access = len([
            entry for entry in self.audit_log
            if (now - datetime.fromisoformat(entry["timestamp"])).total_seconds() < 3600
        ])
        
        # Count failed attempts
        failed_attempts = len([
            entry for entry in self.audit_log
            if not entry.get("success", True)
        ])
        
        return {
            "active_api_keys": active_keys,
            "recent_access_attempts": recent_access,
            "failed_attempts": failed_attempts,
            "total_audit_entries": len(self.audit_log),
            "rate_limit_config": self.rate_limiter.limits
        }

    def reset_rate_limits(self):
        """Resetear rate limits"""
        self.rate_limiter.counters.clear()
        logger.info("Rate limits reset")

    def clear_audit_log(self):
        """Limpiar audit log"""
        self.audit_log.clear()
        logger.info("Audit log cleared")
