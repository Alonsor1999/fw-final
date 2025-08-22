# Diagrama de Flujo de Datos - Framework MVP

## 🔄 Flujo Completo de Procesamiento

```mermaid
flowchart TD
    A[Cliente HTTP] -->|POST /api/v1/robots| B[FastAPI Router]
    B -->|Dependency Injection| C[get_orchestrator]
    C -->|Orchestrator Instance| D[process_robot]
    
    D -->|1. Security Validation| E[SecurityValidator]
    E -->|API Key Check| F{Valid API Key?}
    F -->|No| G[401 Unauthorized]
    F -->|Yes| H[Rate Limit Check]
    H -->|Exceeded| I[429 Too Many Requests]
    H -->|OK| J[Input Sanitization]
    
    J -->|2. Module Selection| K[LoadBalancer]
    K -->|Query Cache| L[CacheManager]
    L -->|Cache Hit| M[Return Cached Module]
    L -->|Cache Miss| N[Query Database]
    N -->|StateManager| O[PostgreSQL]
    O -->|Module Data| P[Calculate Best Module]
    P -->|Cache Result| L
    
    M -->|3. Robot Creation| Q[StateManager.create_robot]
    Q -->|Write Pool| O
    O -->|Robot Created| R[Cache Robot Status]
    R -->|Redis| S[CacheManager.set_robot_status]
    
    S -->|4. Start Execution| T[StateManager.start_execution]
    T -->|Write Pool| O
    O -->|Execution Started| U[Performance Tracking]
    U -->|Record Operation| V[PerformanceTracker]
    
    V -->|5. Module Processing| W[External Module]
    W -->|Processing Result| X[Update Progress]
    X -->|StateManager.update_robot_progress| O
    X -->|Cache Update| S
    
    X -->|6. Completion| Y{Processing Complete?}
    Y -->|No| Z[Continue Processing]
    Z -->|Loop Back| X
    Y -->|Yes| AA[Complete Robot]
    AA -->|StateManager.complete_robot| O
    AA -->|Cache Invalidation| BB[CacheManager.delete_robot_status]
    
    AA -->|7. Response| CC[Return Robot Status]
    CC -->|JSON Response| A
    
    %% Background Processes
    DD[Health Monitor Loop] -->|Every 5min| EE[Check Module Health]
    EE -->|Update Cache| L
    EE -->|Update Database| O
    
    FF[Performance Update Loop] -->|Every 15min| GG[Calculate Performance Scores]
    GG -->|Update Module Scores| O
    GG -->|Update Cache| L
    
    HH[Cleanup Loop] -->|Daily| II[Clean Old Data]
    II -->|Delete Old Executions| O
    II -->|Clean Cache| L
```

## 🏗️ Arquitectura de Capas Detallada

```mermaid
graph TB
    subgraph "Capa de Presentación"
        A[HTTP Client]
        B[Nginx Reverse Proxy]
        C[FastAPI Application]
    end
    
    subgraph "Capa de API"
        D[API Routes]
        E[Dependencies]
        F[Middleware]
    end
    
    subgraph "Capa de Orquestación"
        G[Orchestrator]
        H[Background Tasks]
    end
    
    subgraph "Capa de Servicios Core"
        I[StateManager]
        J[CacheManager]
    end
    
    subgraph "Capa de Servicios Compartidos"
        K[LoadBalancer]
        L[SecurityValidator]
        M[PerformanceTracker]
        N[EmailMonitor]
        O[OCREngine]
        P[NotificationService]
    end
    
    subgraph "Capa de Datos"
        Q[Pydantic Models]
        R[PostgreSQL]
        S[Redis]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    G --> I
    G --> J
    G --> K
    G --> L
    G --> M
    G --> N
    G --> O
    G --> P
    I --> R
    J --> S
    Q --> R
    Q --> S
```

## 🔐 Flujo de Seguridad

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant SecurityValidator
    participant RateLimiter
    participant AuditLogger
    participant Orchestrator
    
    Client->>API: Request with API Key
    API->>SecurityValidator: validate_request()
    
    SecurityValidator->>SecurityValidator: validate_api_key()
    alt Invalid API Key
        SecurityValidator-->>API: 401 Unauthorized
        API-->>Client: Error Response
    else Valid API Key
        SecurityValidator->>RateLimiter: check_rate_limit()
        alt Rate Limit Exceeded
            RateLimiter-->>SecurityValidator: Limit Exceeded
            SecurityValidator-->>API: 429 Too Many Requests
            API-->>Client: Error Response
        else Rate Limit OK
            RateLimiter-->>SecurityValidator: OK
            SecurityValidator->>SecurityValidator: sanitize_input()
            SecurityValidator->>AuditLogger: log_request()
            SecurityValidator-->>Orchestrator: Validation Success
            Orchestrator->>Orchestrator: Process Request
        end
    end
```

## 💾 Flujo de Datos en Base de Datos

```mermaid
graph LR
    subgraph "Read Operations"
        A[CacheManager.get]
        B[StateManager.read_pool]
        C[PostgreSQL Read]
    end
    
    subgraph "Write Operations"
        D[StateManager.write_pool]
        E[PostgreSQL Write]
        F[Cache Invalidation]
    end
    
    subgraph "Transaction Flow"
        G[Begin Transaction]
        H[Execute Operations]
        I[Commit/Rollback]
    end
    
    A -->|Cache Hit| A
    A -->|Cache Miss| B
    B --> C
    D --> E
    E --> F
    G --> H
    H --> I
```

## 🔄 Patrón Circuit Breaker

```mermaid
stateDiagram-v2
    [*] --> Closed
    Closed --> Open : Failure Threshold Reached
    Open --> HalfOpen : Timeout Elapsed
    HalfOpen --> Closed : Success
    HalfOpen --> Open : Failure
    Closed --> [*] : System Shutdown
    Open --> [*] : System Shutdown
    HalfOpen --> [*] : System Shutdown
```

## 📊 Flujo de Métricas y Monitoreo

```mermaid
graph TB
    subgraph "Data Collection"
        A[PerformanceTracker.record_operation]
        B[CacheManager.get_stats]
        C[StateManager.get_metrics]
        D[LoadBalancer.get_performance]
    end
    
    subgraph "Metrics Processing"
        E[Calculate Averages]
        F[Identify Anomalies]
        G[Generate Alerts]
        H[Update Scores]
    end
    
    subgraph "Storage"
        I[Cache Metrics]
        J[Database Metrics]
        K[System Health]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    E --> F
    F --> G
    E --> H
    H --> I
    H --> J
    G --> K
```

## 🚀 Flujo de Escalabilidad

```mermaid
graph LR
    subgraph "Single Instance"
        A[FastAPI App]
        B[PostgreSQL]
        C[Redis]
    end
    
    subgraph "Horizontal Scaling"
        D[Load Balancer]
        E[App Instance 1]
        F[App Instance 2]
        G[App Instance N]
        H[Database Cluster]
        I[Redis Cluster]
    end
    
    A --> B
    A --> C
    D --> E
    D --> F
    D --> G
    E --> H
    F --> H
    G --> H
    E --> I
    F --> I
    G --> I
```

## 🔧 Flujo de Configuración

```mermaid
graph TB
    subgraph "Environment"
        A[Environment Variables]
        B[.env File]
        C[Docker Environment]
    end
    
    subgraph "Configuration"
        D[Settings Class]
        E[Performance Config]
        F[Security Config]
        G[Cache Config]
    end
    
    subgraph "Application"
        H[FastAPI App]
        I[Orchestrator]
        J[Components]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    D --> F
    D --> G
    E --> H
    F --> H
    G --> H
    H --> I
    I --> J
```

## 📝 Resumen de Interacciones

### 1. **Flujo Principal de Robot**
1. **Validación de Seguridad** (5-10ms)
2. **Selección de Módulo** (10-15ms)
3. **Creación de Robot** (20-30ms)
4. **Inicio de Ejecución** (5-10ms)
5. **Procesamiento** (Variable)
6. **Actualización de Estado** (10-15ms)

### 2. **Optimizaciones de Performance**
- **Connection Pooling**: Pools separados para lectura/escritura
- **Caché Inteligente**: TTL dinámico según tipo de dato
- **Prepared Statements**: Prevención de SQL injection
- **Operaciones Asíncronas**: No-blocking I/O

### 3. **Patrones de Resiliencia**
- **Circuit Breaker**: Protección contra fallos en cascada
- **Retry Logic**: Reintentos con backoff exponencial
- **Graceful Degradation**: Funcionalidad reducida en fallos
- **Health Monitoring**: Monitoreo continuo de componentes

### 4. **Capas de Seguridad**
- **API Key Authentication**: Autenticación por clave
- **Rate Limiting**: Protección contra abuso
- **Input Validation**: Sanitización de entrada
- **Audit Logging**: Trazabilidad completa

Este framework implementa una arquitectura robusta y escalable que mantiene la simplicidad del MVP mientras proporciona una base sólida para evolución empresarial.

