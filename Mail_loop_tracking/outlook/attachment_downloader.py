"""
Módulo para descargar adjuntos de correos de Outlook
"""

import os
import requests
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from outlook.graph_client import get_authenticated_session
from config import GRAPH_API_ENDPOINT, MAIL_USER

logger = logging.getLogger(__name__)

class AttachmentDownloader:
    """Clase para descargar adjuntos de correos de Outlook"""
    
    def __init__(self, download_dir: str = "./attachments"):
        """
        Inicializar el descargador de adjuntos
        
        Args:
            download_dir: Directorio donde se guardarán los adjuntos
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.session = get_authenticated_session()
        
        logger.info(f"📁 Directorio de descarga: {self.download_dir.absolute()}")
    
    def get_message_attachments(self, message_id: str) -> List[Dict]:
        """
        Obtener lista de adjuntos de un mensaje
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            List[Dict]: Lista de adjuntos
        """
        try:
            url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/messages/{message_id}/attachments"
            response = self.session.get(url)
            
            if response.ok:
                attachments = response.json().get("value", [])
                logger.info(f"📎 {len(attachments)} adjuntos encontrados para mensaje {message_id}")
                return attachments
            else:
                logger.error(f"❌ Error obteniendo adjuntos: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo adjuntos del mensaje {message_id}: {e}")
            return []
    
    def download_attachment(self, attachment: Dict, message_info: Dict) -> Optional[str]:
        """
        Descargar un adjunto específico
        
        Args:
            attachment: Información del adjunto
            message_info: Información del mensaje (para crear nombre de archivo)
            
        Returns:
            str: Ruta del archivo descargado o None si falló
        """
        try:
            attachment_id = attachment.get("id")
            attachment_name = attachment.get("name", "unknown")
            content_type = attachment.get("contentType", "")
            
            # Crear nombre de archivo único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            message_subject = message_info.get("subject", "unknown").replace(" ", "_")[:30]
            sender = message_info.get("sender", "unknown").split("@")[0]
            
            # Limpiar nombre de archivo
            safe_name = "".join(c for c in attachment_name if c.isalnum() or c in "._-")
            file_extension = Path(attachment_name).suffix
            
            # Crear nombre final
            final_name = f"{timestamp}_{sender}_{message_subject}_{safe_name}"
            if not file_extension and content_type:
                # Intentar inferir extensión del content type
                if "pdf" in content_type.lower():
                    file_extension = ".pdf"
                elif "word" in content_type.lower():
                    file_extension = ".docx"
                elif "excel" in content_type.lower():
                    file_extension = ".xlsx"
                elif "image" in content_type.lower():
                    file_extension = ".jpg"
            
            if file_extension:
                final_name += file_extension
            
            # Crear ruta completa
            file_path = self.download_dir / final_name
            
            # Descargar contenido del adjunto
            if attachment.get("@odata.type") == "#microsoft.graph.fileAttachment":
                # Adjunto de archivo
                content_url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/messages/{message_info['id']}/attachments/{attachment_id}/$value"
                response = self.session.get(content_url)
                
                if response.ok:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"✅ Adjunto descargado: {file_path.name} ({len(response.content)} bytes)")
                    return str(file_path.absolute())
                else:
                    logger.error(f"❌ Error descargando adjunto {attachment_name}: {response.status_code}")
                    return None
            
            elif attachment.get("@odata.type") == "#microsoft.graph.itemAttachment":
                # Adjunto de item (otro mensaje, etc.)
                logger.warning(f"⚠️ Adjunto de tipo item no soportado: {attachment_name}")
                return None
            
            else:
                logger.warning(f"⚠️ Tipo de adjunto no reconocido: {attachment.get('@odata.type')}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error descargando adjunto {attachment.get('name', 'unknown')}: {e}")
            return None
    
    def download_message_attachments(self, message: Dict) -> List[str]:
        """
        Descargar todos los adjuntos de un mensaje
        
        Args:
            message: Mensaje de correo
            
        Returns:
            List[str]: Lista de rutas de archivos descargados
        """
        message_id = message.get("id")
        if not message_id:
            logger.error("❌ Mensaje sin ID")
            return []
        
        # Extraer información del mensaje
        message_info = {
            "id": message_id,
            "subject": message.get("subject", ""),
            "sender": self._extract_sender_email(message),
            "received_date": message.get("receivedDateTime", "")
        }
        
        # Obtener adjuntos
        attachments = self.get_message_attachments(message_id)
        if not attachments:
            logger.info(f"📧 Mensaje sin adjuntos: {message_info['subject']}")
            return []
        
        # Descargar cada adjunto
        downloaded_files = []
        for attachment in attachments:
            file_path = self.download_attachment(attachment, message_info)
            if file_path:
                downloaded_files.append(file_path)
        
        logger.info(f"📎 {len(downloaded_files)}/{len(attachments)} adjuntos descargados para: {message_info['subject']}")
        return downloaded_files
    
    def download_pdf_attachments(self, message: Dict) -> List[str]:
        """
        Descargar solo adjuntos PDF de un mensaje
        
        Args:
            message: Mensaje de correo
            
        Returns:
            List[str]: Lista de rutas de PDFs descargados
        """
        message_id = message.get("id")
        if not message_id:
            logger.error("❌ Mensaje sin ID")
            return []
        
        # Obtener adjuntos
        attachments = self.get_message_attachments(message_id)
        if not attachments:
            return []
        
        # Filtrar solo PDFs
        pdf_attachments = []
        for attachment in attachments:
            attachment_name = attachment.get("name", "").lower()
            content_type = attachment.get("contentType", "").lower()
            
            if (attachment_name.endswith('.pdf') or 
                'pdf' in content_type or 
                'application/pdf' in content_type):
                pdf_attachments.append(attachment)
        
        if not pdf_attachments:
            logger.info(f"📧 Mensaje sin adjuntos PDF: {message.get('subject', '')}")
            return []
        
        # Extraer información del mensaje
        message_info = {
            "id": message_id,
            "subject": message.get("subject", ""),
            "sender": self._extract_sender_email(message),
            "received_date": message.get("receivedDateTime", "")
        }
        
        # Descargar PDFs
        downloaded_pdfs = []
        for attachment in pdf_attachments:
            file_path = self.download_attachment(attachment, message_info)
            if file_path and file_path.lower().endswith('.pdf'):
                downloaded_pdfs.append(file_path)
        
        logger.info(f"📄 {len(downloaded_pdfs)} PDFs descargados para: {message_info['subject']}")
        return downloaded_pdfs
    
    def _extract_sender_email(self, message: Dict) -> str:
        """Extraer email del remitente"""
        sender = message.get('from', {})
        if isinstance(sender, dict):
            email = sender.get('emailAddress', {}).get('address', '')
        else:
            email = str(sender)
        return email
    
    def get_download_stats(self) -> Dict:
        """Obtener estadísticas de descarga"""
        try:
            files = list(self.download_dir.glob("*"))
            total_files = len(files)
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            
            # Contar por tipo de archivo
            file_types = {}
            for file in files:
                if file.is_file():
                    ext = file.suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "download_dir": str(self.download_dir.absolute())
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    def cleanup_old_files(self, days: int = 7):
        """
        Limpiar archivos antiguos
        
        Args:
            days: Número de días para considerar archivo como antiguo
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            deleted_count = 0
            for file in self.download_dir.glob("*"):
                if file.is_file():
                    file_time = datetime.fromtimestamp(file.stat().st_mtime)
                    if file_time < cutoff_date:
                        file.unlink()
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"🗑️ {deleted_count} archivos antiguos eliminados")
            
        except Exception as e:
            logger.error(f"❌ Error limpiando archivos antiguos: {e}")
