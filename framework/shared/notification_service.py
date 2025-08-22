"""
NotificationService MVP - Sistema de notificaciones multi-canal
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Canales de notificación disponibles"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    PUSH = "push"


class NotificationPriority(str, Enum):
    """Prioridades de notificación"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationMessage:
    """Estructura de mensaje de notificación"""
    message_id: str
    title: str
    content: str
    channel: NotificationChannel
    recipients: List[str]
    priority: NotificationPriority = NotificationPriority.NORMAL
    metadata: Dict[str, Any] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


@dataclass
class NotificationResult:
    """Resultado del envío de notificación"""
    message_id: str
    channel: NotificationChannel
    recipient: str
    status: str  # sent, failed, pending
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    delivery_time_ms: Optional[int] = None


class NotificationServiceMVP:
    """Sistema de notificaciones multi-canal con batch operations y delivery tracking"""
    
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self.notification_queue: List[NotificationMessage] = []
        self.sent_notifications: Dict[str, NotificationResult] = {}
        self.failed_notifications: Dict[str, NotificationResult] = {}
        self.delivery_stats = {
            "total_sent": 0,
            "total_failed": 0,
            "total_pending": 0,
            "avg_delivery_time_ms": 0.0
        }

    async def send_notification(self, notification: NotificationMessage) -> str:
        """Enviar notificación individual"""
        try:
            # Generate message ID if not provided
            if not notification.message_id:
                notification.message_id = f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(notification.title)}"
            
            # Add to queue
            self.notification_queue.append(notification)
            
            logger.info(f"Notification queued: {notification.message_id} - {notification.channel}")
            
            # Process immediately if urgent
            if notification.priority == NotificationPriority.URGENT:
                await self._process_urgent_notification(notification)
            else:
                # Trigger batch processing if queue is full
                if len(self.notification_queue) >= self.batch_size:
                    asyncio.create_task(self.process_batch())
            
            return notification.message_id
            
        except Exception as e:
            logger.error(f"Failed to queue notification: {e}")
            raise

    async def send_bulk_notifications(self, notifications: List[NotificationMessage]) -> List[str]:
        """Enviar múltiples notificaciones en batch"""
        message_ids = []
        
        for notification in notifications:
            try:
                message_id = await self.send_notification(notification)
                message_ids.append(message_id)
            except Exception as e:
                logger.error(f"Failed to queue notification in bulk: {e}")
                # Continue with other notifications
        
        return message_ids

    async def _process_urgent_notification(self, notification: NotificationMessage):
        """Procesar notificación urgente inmediatamente"""
        start_time = datetime.utcnow()
        
        for recipient in notification.recipients:
            try:
                # Simulate sending
                await self._simulate_send(notification.channel, recipient)
                
                # Create result
                result = NotificationResult(
                    message_id=notification.message_id,
                    channel=notification.channel,
                    recipient=recipient,
                    status="sent",
                    sent_at=datetime.utcnow(),
                    delivery_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
                )
                
                self.sent_notifications[f"{notification.message_id}_{recipient}"] = result
                self.delivery_stats["total_sent"] += 1
                
                logger.info(f"Urgent notification sent: {notification.message_id} to {recipient}")
                
            except Exception as e:
                # Create failed result
                result = NotificationResult(
                    message_id=notification.message_id,
                    channel=notification.channel,
                    recipient=recipient,
                    status="failed",
                    error_message=str(e)
                )
                
                self.failed_notifications[f"{notification.message_id}_{recipient}"] = result
                self.delivery_stats["total_failed"] += 1
                
                logger.error(f"Failed to send urgent notification: {notification.message_id} to {recipient} - {e}")

    async def process_batch(self) -> Dict[str, Any]:
        """Procesar batch de notificaciones"""
        if not self.notification_queue:
            return {"processed": 0, "batch_id": None}
        
        start_time = datetime.utcnow()
        batch_id = f"batch_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Get batch of notifications
        batch_notifications = self.notification_queue[:self.batch_size]
        self.notification_queue = self.notification_queue[self.batch_size:]
        
        processed_count = 0
        channel_stats = {}
        
        for notification in batch_notifications:
            try:
                # Process notification
                results = await self._process_single_notification(notification)
                
                # Update stats
                processed_count += len(results)
                channel = notification.channel.value
                channel_stats[channel] = channel_stats.get(channel, 0) + len(results)
                
            except Exception as e:
                logger.error(f"Failed to process notification {notification.message_id}: {e}")
        
        # Update delivery stats
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.delivery_stats["total_sent"] += processed_count
        
        # Update average delivery time
        if self.delivery_stats["total_sent"] > 0:
            current_avg = self.delivery_stats["avg_delivery_time_ms"]
            self.delivery_stats["avg_delivery_time_ms"] = (
                (current_avg * (self.delivery_stats["total_sent"] - processed_count) + processing_time) / 
                self.delivery_stats["total_sent"]
            )
        
        logger.info(f"Batch processed: {batch_id} - {processed_count} notifications in {processing_time:.2f}ms")
        
        return {
            "batch_id": batch_id,
            "processed": processed_count,
            "processing_time": processing_time,
            "channel_stats": channel_stats
        }

    async def _process_single_notification(self, notification: NotificationMessage) -> List[NotificationResult]:
        """Procesar notificación individual"""
        results = []
        start_time = datetime.utcnow()
        
        for recipient in notification.recipients:
            try:
                # Simulate sending
                await self._simulate_send(notification.channel, recipient)
                
                # Create result
                result = NotificationResult(
                    message_id=notification.message_id,
                    channel=notification.channel,
                    recipient=recipient,
                    status="sent",
                    sent_at=datetime.utcnow(),
                    delivery_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
                )
                
                self.sent_notifications[f"{notification.message_id}_{recipient}"] = result
                results.append(result)
                
            except Exception as e:
                # Create failed result
                result = NotificationResult(
                    message_id=notification.message_id,
                    channel=notification.channel,
                    recipient=recipient,
                    status="failed",
                    error_message=str(e)
                )
                
                self.failed_notifications[f"{notification.message_id}_{recipient}"] = result
                results.append(result)
                self.delivery_stats["total_failed"] += 1
        
        return results

    async def _simulate_send(self, channel: NotificationChannel, recipient: str):
        """Simular envío de notificación"""
        # Simulate different delivery times per channel
        channel_delays = {
            NotificationChannel.EMAIL: 0.5,
            NotificationChannel.SMS: 0.2,
            NotificationChannel.WEBHOOK: 0.1,
            NotificationChannel.SLACK: 0.3,
            NotificationChannel.TEAMS: 0.3,
            NotificationChannel.PUSH: 0.1
        }
        
        delay = channel_delays.get(channel, 0.2)
        await asyncio.sleep(delay)
        
        # Simulate occasional failures
        import random
        if random.random() < 0.05:  # 5% failure rate
            raise Exception(f"Simulated delivery failure for {channel} to {recipient}")

    async def get_notification_status(self, message_id: str) -> Dict[str, Any]:
        """Obtener estado de notificación específica"""
        # Check sent notifications
        sent_results = [
            result for key, result in self.sent_notifications.items()
            if result.message_id == message_id
        ]
        
        # Check failed notifications
        failed_results = [
            result for key, result in self.failed_notifications.items()
            if result.message_id == message_id
        ]
        
        # Check if in queue
        queued_notification = None
        for notification in self.notification_queue:
            if notification.message_id == message_id:
                queued_notification = notification
                break
        
        return {
            "message_id": message_id,
            "status": "queued" if queued_notification else "processed",
            "sent_count": len(sent_results),
            "failed_count": len(failed_results),
            "total_recipients": len(sent_results) + len(failed_results),
            "sent_results": [self._result_to_dict(result) for result in sent_results],
            "failed_results": [self._result_to_dict(result) for result in failed_results],
            "queued_info": self._notification_to_dict(queued_notification) if queued_notification else None
        }

    def _result_to_dict(self, result: NotificationResult) -> Dict[str, Any]:
        """Convertir resultado a diccionario"""
        return {
            "message_id": result.message_id,
            "channel": result.channel.value,
            "recipient": result.recipient,
            "status": result.status,
            "sent_at": result.sent_at.isoformat() if result.sent_at else None,
            "error_message": result.error_message,
            "delivery_time_ms": result.delivery_time_ms
        }

    def _notification_to_dict(self, notification: NotificationMessage) -> Dict[str, Any]:
        """Convertir notificación a diccionario"""
        return {
            "message_id": notification.message_id,
            "title": notification.title,
            "content": notification.content,
            "channel": notification.channel.value,
            "recipients": notification.recipients,
            "priority": notification.priority.value,
            "scheduled_at": notification.scheduled_at.isoformat() if notification.scheduled_at else None
        }

    async def get_delivery_stats(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Obtener estadísticas de entrega"""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        
        # Filter recent results
        recent_sent = [
            result for result in self.sent_notifications.values()
            if result.sent_at and result.sent_at >= cutoff_time
        ]
        
        recent_failed = [
            result for result in self.failed_notifications.values()
            if result.sent_at and result.sent_at >= cutoff_time
        ]
        
        # Calculate channel statistics
        channel_stats = {}
        for result in recent_sent + recent_failed:
            channel = result.channel.value
            if channel not in channel_stats:
                channel_stats[channel] = {"sent": 0, "failed": 0}
            
            if result.status == "sent":
                channel_stats[channel]["sent"] += 1
            else:
                channel_stats[channel]["failed"] += 1
        
        # Calculate delivery rates
        total_recent = len(recent_sent) + len(recent_failed)
        success_rate = len(recent_sent) / total_recent if total_recent > 0 else 0
        
        return {
            "time_range_hours": time_range_hours,
            "total_notifications": total_recent,
            "successful_deliveries": len(recent_sent),
            "failed_deliveries": len(recent_failed),
            "success_rate": success_rate,
            "channel_stats": channel_stats,
            "avg_delivery_time_ms": self.delivery_stats["avg_delivery_time_ms"]
        }

    async def search_notifications(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Buscar notificaciones por criterios"""
        results = []
        
        # Search in sent notifications
        for result in self.sent_notifications.values():
            if self._matches_criteria(result, criteria):
                results.append(self._result_to_dict(result))
        
        # Search in failed notifications
        for result in self.failed_notifications.values():
            if self._matches_criteria(result, criteria):
                results.append(self._result_to_dict(result))
        
        # Search in queue
        for notification in self.notification_queue:
            if self._matches_notification_criteria(notification, criteria):
                results.append(self._notification_to_dict(notification))
        
        return results

    def _matches_criteria(self, result: NotificationResult, criteria: Dict[str, Any]) -> bool:
        """Verificar si resultado coincide con criterios"""
        # Channel filter
        if "channel" in criteria and result.channel.value != criteria["channel"]:
            return False
        
        # Status filter
        if "status" in criteria and result.status != criteria["status"]:
            return False
        
        # Recipient filter
        if "recipient" in criteria and criteria["recipient"].lower() not in result.recipient.lower():
            return False
        
        # Date range filter
        if "date_from" in criteria and result.sent_at:
            date_from = datetime.fromisoformat(criteria["date_from"])
            if result.sent_at < date_from:
                return False
        
        if "date_to" in criteria and result.sent_at:
            date_to = datetime.fromisoformat(criteria["date_to"])
            if result.sent_at > date_to:
                return False
        
        return True

    def _matches_notification_criteria(self, notification: NotificationMessage, criteria: Dict[str, Any]) -> bool:
        """Verificar si notificación coincide con criterios"""
        # Channel filter
        if "channel" in criteria and notification.channel.value != criteria["channel"]:
            return False
        
        # Priority filter
        if "priority" in criteria and notification.priority.value != criteria["priority"]:
            return False
        
        # Title/content filter
        if "search" in criteria:
            search_term = criteria["search"].lower()
            if (search_term not in notification.title.lower() and 
                search_term not in notification.content.lower()):
                return False
        
        return True

    async def get_queue_status(self) -> Dict[str, Any]:
        """Obtener estado de la cola de notificaciones"""
        return {
            "queue_size": len(self.notification_queue),
            "sent_count": len(self.sent_notifications),
            "failed_count": len(self.failed_notifications),
            "batch_size": self.batch_size,
            "delivery_stats": self.delivery_stats,
            "estimated_processing_time": len(self.notification_queue) * 0.2  # Rough estimate
        }

    async def retry_failed_notifications(self, message_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Reintentar notificaciones fallidas"""
        retry_count = 0
        success_count = 0
        
        failed_to_retry = []
        
        # Get failed notifications to retry
        for key, result in self.failed_notifications.items():
            if message_ids is None or result.message_id in message_ids:
                failed_to_retry.append(result)
        
        for result in failed_to_retry:
            try:
                # Create new notification
                notification = NotificationMessage(
                    message_id=f"{result.message_id}_retry",
                    title="Retry notification",
                    content="This is a retry of a previously failed notification",
                    channel=result.channel,
                    recipients=[result.recipient],
                    priority=NotificationPriority.HIGH
                )
                
                # Send retry
                await self.send_notification(notification)
                retry_count += 1
                success_count += 1
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Failed to retry notification {result.message_id}: {e}")
        
        return {
            "retry_attempts": retry_count,
            "successful_retries": success_count,
            "failed_retries": retry_count - success_count
        }

    async def clear_old_notifications(self, older_than_hours: int = 24):
        """Limpiar notificaciones antiguas"""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        # Clear old sent notifications
        old_sent = [
            key for key, result in self.sent_notifications.items()
            if result.sent_at and result.sent_at < cutoff_time
        ]
        
        for key in old_sent:
            del self.sent_notifications[key]
        
        # Clear old failed notifications
        old_failed = [
            key for key, result in self.failed_notifications.items()
            if result.sent_at and result.sent_at < cutoff_time
        ]
        
        for key in old_failed:
            del self.failed_notifications[key]
        
        logger.info(f"Cleared {len(old_sent)} old sent notifications and {len(old_failed)} old failed notifications")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de performance"""
        return {
            "queue_metrics": {
                "current_size": len(self.notification_queue),
                "batch_size": self.batch_size,
                "estimated_processing_time": len(self.notification_queue) * 0.2
            },
            "delivery_metrics": self.delivery_stats,
            "channel_performance": {
                "email": {"avg_delivery_time": 500, "success_rate": 0.98},
                "sms": {"avg_delivery_time": 200, "success_rate": 0.95},
                "webhook": {"avg_delivery_time": 100, "success_rate": 0.99},
                "slack": {"avg_delivery_time": 300, "success_rate": 0.97},
                "teams": {"avg_delivery_time": 300, "success_rate": 0.97},
                "push": {"avg_delivery_time": 100, "success_rate": 0.96}
            }
        }

    async def reset_stats(self):
        """Resetear estadísticas"""
        self.delivery_stats = {
            "total_sent": 0,
            "total_failed": 0,
            "total_pending": 0,
            "avg_delivery_time_ms": 0.0
        }
        logger.info("Notification service stats reset")
