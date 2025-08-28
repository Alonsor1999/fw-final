"""
Capa de Procesamiento de Email - Robot001
Maneja operaciones específicas de correo electrónico para Outlook
"""

from .outlook_email_processor import OutlookEmailProcessor
from .email_coordinator import EmailCoordinator

__all__ = [
    'OutlookEmailProcessor',
    'EmailCoordinator'
]
