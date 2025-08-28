"""
Utilidades para manejo robusto de errores y reintentos.

Este módulo proporciona decoradores y funciones para:
- Reintentos automáticos con backoff exponencial
- Manejo específico de errores de API
- Rate limiting básico
"""
import time
import random
from functools import wraps
from typing import Callable, Any, Optional, Type, Union, List
from utils.logger_config import setup_logger

logger = setup_logger("retry_utils")

class GraphAPIError(Exception):
    """Error base para Microsoft Graph API"""
    pass

class AuthenticationError(GraphAPIError):
    """Error de autenticación con Microsoft Graph API"""
    pass

class RateLimitError(GraphAPIError):
    """Error de rate limiting"""
    pass

class NetworkError(GraphAPIError):
    """Error de red o conectividad"""
    pass

class MessageProcessingError(GraphAPIError):
    """Error en procesamiento de mensajes"""
    pass

def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    jitter: bool = True
):
    """
    Decorador para reintentos automáticos con backoff exponencial.
    
    Args:
        max_retries: Número máximo de reintentos
        delay: Delay inicial en segundos
        backoff_factor: Factor de multiplicación para el delay
        exceptions: Excepción(es) que deben causar reintento
        jitter: Si agregar variación aleatoria al delay
        
    Returns:
        Decorador que aplica la lógica de reintentos
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"❌ Función {func.__name__} falló después de {max_retries} reintentos: {e}")
                        raise
                    
                    # Calcular delay con backoff exponencial
                    current_delay = delay * (backoff_factor ** attempt)
                    
                    # Agregar jitter si está habilitado
                    if jitter:
                        jitter_amount = current_delay * 0.1  # 10% de jitter
                        current_delay += random.uniform(-jitter_amount, jitter_amount)
                        current_delay = max(0.1, current_delay)  # Mínimo 0.1 segundos
                    
                    logger.warning(
                        f"⚠️ Intento {attempt + 1}/{max_retries + 1} falló en {func.__name__}: {e}. "
                        f"Reintentando en {current_delay:.2f}s..."
                    )
                    
                    time.sleep(current_delay)
            
            # Nunca debería llegar aquí, pero por seguridad
            raise last_exception
            
        return wrapper
    return decorator

def handle_graph_api_errors(func: Callable) -> Callable:
    """
    Decorador para manejo específico de errores de Microsoft Graph API.
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada con manejo de errores específicos
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Clasificar errores específicos
            if "unauthorized" in error_msg or "forbidden" in error_msg:
                raise AuthenticationError(f"Error de autenticación: {e}")
            elif "too many requests" in error_msg or "429" in error_msg:
                raise RateLimitError(f"Rate limit excedido: {e}")
            elif "timeout" in error_msg or "connection" in error_msg:
                raise NetworkError(f"Error de conectividad: {e}")
            else:
                # Re-raise como GraphAPIError genérico
                raise GraphAPIError(f"Error de Microsoft Graph API: {e}")
    
    return wrapper

def rate_limit(max_calls: int = 100, time_window: float = 60.0):
    """
    Decorador para rate limiting básico.
    
    Args:
        max_calls: Número máximo de llamadas permitidas
        time_window: Ventana de tiempo en segundos
        
    Returns:
        Decorador que aplica rate limiting
    """
    def decorator(func: Callable) -> Callable:
        # Variables para tracking
        call_times = []
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_time = time.time()
            
            # Limpiar llamadas fuera de la ventana de tiempo
            call_times[:] = [t for t in call_times if current_time - t < time_window]
            
            # Verificar si se excedió el límite
            if len(call_times) >= max_calls:
                sleep_time = time_window - (current_time - call_times[0])
                if sleep_time > 0:
                    logger.warning(f"⚠️ Rate limit alcanzado. Esperando {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
            
            # Registrar la llamada actual
            call_times.append(current_time)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def exponential_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """
    Decorador con backoff exponencial más sofisticado.
    
    Args:
        max_retries: Número máximo de reintentos
        base_delay: Delay base en segundos
        max_delay: Delay máximo en segundos
        
    Returns:
        Decorador con backoff exponencial
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"❌ Función {func.__name__} falló definitivamente: {e}")
                        raise
                    
                    # Calcular delay con backoff exponencial
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    # Agregar jitter
                    jitter = delay * 0.1 * random.random()
                    delay += jitter
                    
                    logger.warning(
                        f"⚠️ Intento {attempt + 1}/{max_retries + 1} falló en {func.__name__}. "
                        f"Reintentando en {delay:.2f}s... Error: {e}"
                    )
                    
                    time.sleep(delay)
            
            # Nunca debería llegar aquí
            raise Exception("Error inesperado en exponential_backoff")
        
        return wrapper
    return decorator

def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception
):
    """
    Decorador que implementa el patrón Circuit Breaker.
    
    Args:
        failure_threshold: Número de fallos antes de abrir el circuito
        recovery_timeout: Tiempo de espera antes de intentar cerrar el circuito
        expected_exception: Excepción que se considera como fallo
        
    Returns:
        Decorador con circuit breaker
    """
    def decorator(func: Callable) -> Callable:
        # Estado del circuit breaker
        failure_count = 0
        last_failure_time = 0
        circuit_open = False
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal failure_count, last_failure_time, circuit_open
            
            current_time = time.time()
            
            # Verificar si el circuito está abierto
            if circuit_open:
                if current_time - last_failure_time >= recovery_timeout:
                    logger.info(f"🔄 Circuito semi-abierto para {func.__name__}, probando...")
                    circuit_open = False
                else:
                    raise GraphAPIError(f"Circuito abierto para {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                # Éxito: resetear contador de fallos
                failure_count = 0
                return result
                
            except expected_exception as e:
                failure_count += 1
                last_failure_time = current_time
                
                if failure_count >= failure_threshold:
                    circuit_open = True
                    logger.error(f"🔴 Circuito abierto para {func.__name__} después de {failure_count} fallos")
                
                raise
        
        return wrapper
    return decorator 