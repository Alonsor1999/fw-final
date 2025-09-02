"""
Modelo simple para la tabla de cédulas y fechas de expedición
"""
from pydantic import BaseModel, Field, validator
from typing import Optional


class CedulaSimple(BaseModel):
    """Modelo simple para cédulas y fechas de expedición"""
    
    cedula: str = Field(..., description="Número de cédula de ciudadanía", max_length=20)
    fecha_expedicion: str = Field(..., description="Fecha de expedición en formato texto", max_length=100)
    
    @validator('cedula')
    def validate_cedula(cls, v):
        """Validar formato de cédula"""
        if not v or len(v.strip()) == 0:
            raise ValueError("La cédula no puede estar vacía")
        return v.strip()
    
    @validator('fecha_expedicion')
    def validate_fecha_expedicion(cls, v):
        """Validar fecha de expedición"""
        if not v or len(v.strip()) == 0:
            raise ValueError("La fecha de expedición no puede estar vacía")
        return v.strip()


class CedulaResponse(BaseModel):
    """Modelo para respuestas de cédulas"""
    
    cedula: str
    fecha_expedicion: str
    
    class Config:
        from_attributes = True
