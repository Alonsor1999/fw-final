"""
EmailMonitor MVP - Sistema de monitoreo y procesamiento de emails
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Estructura de datos para mensajes de email"""
    message_id: str
    sender: str
    recipients: List[str]
    subject: str
    body: str
    attachments: List[str]
    received_at: datetime
    priority: str = "normal"
    classification: Optional[str] = None
    processed: bool = False


class EmailClassifierMVP:
    """Clasificador de emails usando reglas simples"""
    
    def __init__(self):
        self.classification_rules = {
            "urgent": [
                "urgent", "asap", "emergency", "critical", "immediate",
                "urgente", "inmediato", "crítico", "emergencia"
            ],
            "spam": [
                "free", "offer", "discount", "limited time", "act now",
                "gratis", "oferta", "descuento", "tiempo limitado"
            ],
            "legal": [
                "contract", "agreement", "legal", "compliance", "regulation",
                "contrato", "acuerdo", "legal", "cumplimiento"
            ],
            "support": [
                "help", "support", "issue", "problem", "ticket",
                "ayuda", "soporte", "problema", "incidente"
            ]
        }

    def classify_email(self, email: EmailMessage) -> str:
        """Clasificar email basado en contenido"""
        content = f"{email.subject} {email.body}".lower()
        
        # Check each classification
        for classification, keywords in self.classification_rules.items():
            for keyword in keywords:
                if keyword in content:
                    return classification
        
        return "general"

    def get_priority_score(self, email: EmailMessage) -> int:
        """Calcular score de prioridad"""
        score = 0
        
        # Base score
        if email.priority == "high":
            score += 10
        elif email.priority == "normal":
            score += 5
        else:
            score += 1
        
        # Classification bonus
        if email.classification == "urgent":
            score += 15
        elif email.classification == "legal":
            score += 8
        elif email.classification == "support":
            score += 5
        
        # Time-based urgency
        hours_old = (datetime.utcnow() - email.received_at).total_seconds() / 3600
        if hours_old > 24:
            score += 3
        elif hours_old > 12:
            score += 2
        elif hours_old > 6:
            score += 1
        
        return score


class EmailMonitorMVP:
    """Sistema de monitoreo de emails con batch processing y ML classification"""
    
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self.classifier = EmailClassifierMVP()
        self.email_queue: List[EmailMessage] = []
        self.processed_emails: Dict[str, EmailMessage] = {}
        self.processing_stats = {
            "total_processed": 0,
            "total_classified": 0,
            "batch_count": 0,
            "avg_processing_time": 0.0
        }

    async def add_email(self, email_data: Dict[str, Any]) -> str:
        """Agregar email al sistema de monitoreo"""
        try:
            # Create email message
            email = EmailMessage(
                message_id=email_data.get("message_id", f"email_{datetime.utcnow().timestamp()}"),
                sender=email_data.get("sender", ""),
                recipients=email_data.get("recipients", []),
                subject=email_data.get("subject", ""),
                body=email_data.get("body", ""),
                attachments=email_data.get("attachments", []),
                received_at=datetime.fromisoformat(email_data.get("received_at", datetime.utcnow().isoformat())),
                priority=email_data.get("priority", "normal")
            )
            
            # Classify email
            email.classification = self.classifier.classify_email(email)
            
            # Add to queue
            self.email_queue.append(email)
            
            logger.info(f"Email added to queue: {email.message_id} - {email.classification}")
            
            # Trigger batch processing if queue is full
            if len(self.email_queue) >= self.batch_size:
                asyncio.create_task(self.process_batch())
            
            return email.message_id
            
        except Exception as e:
            logger.error(f"Failed to add email: {e}")
            raise

    async def process_batch(self) -> Dict[str, Any]:
        """Procesar batch de emails"""
        if not self.email_queue:
            return {"processed": 0, "batch_id": None}
        
        start_time = datetime.utcnow()
        batch_id = f"batch_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Get batch of emails
        batch_emails = self.email_queue[:self.batch_size]
        self.email_queue = self.email_queue[self.batch_size:]
        
        processed_count = 0
        classification_stats = {}
        
        for email in batch_emails:
            try:
                # Process email
                await self._process_single_email(email)
                
                # Update stats
                processed_count += 1
                classification = email.classification or "unknown"
                classification_stats[classification] = classification_stats.get(classification, 0) + 1
                
                # Store processed email
                self.processed_emails[email.message_id] = email
                
            except Exception as e:
                logger.error(f"Failed to process email {email.message_id}: {e}")
        
        # Update processing stats
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        self.processing_stats["total_processed"] += processed_count
        self.processing_stats["total_classified"] += processed_count
        self.processing_stats["batch_count"] += 1
        
        # Update average processing time
        total_batches = self.processing_stats["batch_count"]
        current_avg = self.processing_stats["avg_processing_time"]
        self.processing_stats["avg_processing_time"] = (
            (current_avg * (total_batches - 1) + processing_time) / total_batches
        )
        
        logger.info(f"Batch processed: {batch_id} - {processed_count} emails in {processing_time:.2f}s")
        
        return {
            "batch_id": batch_id,
            "processed": processed_count,
            "processing_time": processing_time,
            "classification_stats": classification_stats
        }

    async def _process_single_email(self, email: EmailMessage):
        """Procesar email individual"""
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Mark as processed
        email.processed = True
        
        # Log processing
        logger.debug(f"Processed email: {email.message_id} - {email.classification}")

    async def get_email_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de email específico"""
        if message_id in self.processed_emails:
            email = self.processed_emails[message_id]
            return {
                "message_id": email.message_id,
                "status": "processed" if email.processed else "pending",
                "classification": email.classification,
                "priority": email.priority,
                "received_at": email.received_at.isoformat(),
                "processed_at": datetime.utcnow().isoformat() if email.processed else None
            }
        
        # Check if in queue
        for email in self.email_queue:
            if email.message_id == message_id:
                return {
                    "message_id": email.message_id,
                    "status": "queued",
                    "classification": email.classification,
                    "priority": email.priority,
                    "received_at": email.received_at.isoformat(),
                    "queue_position": self.email_queue.index(email) + 1
                }
        
        return None

    async def get_queue_status(self) -> Dict[str, Any]:
        """Obtener estado de la cola de emails"""
        return {
            "queue_size": len(self.email_queue),
            "processed_count": len(self.processed_emails),
            "batch_size": self.batch_size,
            "processing_stats": self.processing_stats,
            "estimated_wait_time": len(self.email_queue) * 0.1  # Rough estimate
        }

    async def get_classification_stats(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Obtener estadísticas de clasificación"""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        
        # Count classifications in processed emails
        classification_counts = {}
        recent_processed = 0
        
        for email in self.processed_emails.values():
            if email.received_at >= cutoff_time:
                recent_processed += 1
                classification = email.classification or "unknown"
                classification_counts[classification] = classification_counts.get(classification, 0) + 1
        
        # Count classifications in queue
        queue_classifications = {}
        for email in self.email_queue:
            classification = email.classification or "unknown"
            queue_classifications[classification] = queue_classifications.get(classification, 0) + 1
        
        return {
            "time_range_hours": time_range_hours,
            "recent_processed": recent_processed,
            "processed_classifications": classification_counts,
            "queue_classifications": queue_classifications,
            "total_classifications": {
                classification: classification_counts.get(classification, 0) + queue_classifications.get(classification, 0)
                for classification in set(classification_counts.keys()) | set(queue_classifications.keys())
            }
        }

    async def search_emails(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Buscar emails por criterios"""
        results = []
        
        # Search in processed emails
        for email in self.processed_emails.values():
            if self._matches_criteria(email, criteria):
                results.append(self._email_to_dict(email))
        
        # Search in queue
        for email in self.email_queue:
            if self._matches_criteria(email, criteria):
                results.append(self._email_to_dict(email))
        
        return results

    def _matches_criteria(self, email: EmailMessage, criteria: Dict[str, Any]) -> bool:
        """Verificar si email coincide con criterios de búsqueda"""
        # Sender filter
        if "sender" in criteria and criteria["sender"].lower() not in email.sender.lower():
            return False
        
        # Subject filter
        if "subject" in criteria and criteria["subject"].lower() not in email.subject.lower():
            return False
        
        # Classification filter
        if "classification" in criteria and email.classification != criteria["classification"]:
            return False
        
        # Priority filter
        if "priority" in criteria and email.priority != criteria["priority"]:
            return False
        
        # Date range filter
        if "date_from" in criteria:
            date_from = datetime.fromisoformat(criteria["date_from"])
            if email.received_at < date_from:
                return False
        
        if "date_to" in criteria:
            date_to = datetime.fromisoformat(criteria["date_to"])
            if email.received_at > date_to:
                return False
        
        return True

    def _email_to_dict(self, email: EmailMessage) -> Dict[str, Any]:
        """Convertir email a diccionario"""
        return {
            "message_id": email.message_id,
            "sender": email.sender,
            "recipients": email.recipients,
            "subject": email.subject,
            "body": email.body[:200] + "..." if len(email.body) > 200 else email.body,  # Truncate body
            "attachments": email.attachments,
            "received_at": email.received_at.isoformat(),
            "priority": email.priority,
            "classification": email.classification,
            "processed": email.processed,
            "priority_score": self.classifier.get_priority_score(email)
        }

    async def get_priority_queue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener cola de prioridad de emails"""
        # Combine queue and recent processed emails
        all_emails = self.email_queue + list(self.processed_emails.values())
        
        # Sort by priority score
        sorted_emails = sorted(
            all_emails,
            key=lambda email: self.classifier.get_priority_score(email),
            reverse=True
        )
        
        return [self._email_to_dict(email) for email in sorted_emails[:limit]]

    async def clear_processed_emails(self, older_than_hours: int = 24):
        """Limpiar emails procesados antiguos"""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        emails_to_remove = [
            message_id for message_id, email in self.processed_emails.items()
            if email.received_at < cutoff_time
        ]
        
        for message_id in emails_to_remove:
            del self.processed_emails[message_id]
        
        logger.info(f"Cleared {len(emails_to_remove)} old processed emails")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de performance"""
        return {
            "queue_metrics": {
                "current_size": len(self.email_queue),
                "batch_size": self.batch_size,
                "estimated_processing_time": len(self.email_queue) * 0.1
            },
            "processing_metrics": self.processing_stats,
            "classification_metrics": {
                "total_classified": self.processing_stats["total_classified"],
                "avg_batch_time": self.processing_stats["avg_processing_time"],
                "throughput": self.processing_stats["total_processed"] / max(1, self.processing_stats["batch_count"])
            }
        }

    async def reset_stats(self):
        """Resetear estadísticas"""
        self.processing_stats = {
            "total_processed": 0,
            "total_classified": 0,
            "batch_count": 0,
            "avg_processing_time": 0.0
        }
        logger.info("Email monitor stats reset")
