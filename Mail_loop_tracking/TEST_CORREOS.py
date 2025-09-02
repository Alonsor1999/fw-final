"""
Script de pruebas para buscar correos del año 2024.

Este script busca y analiza correos electrónicos únicamente del año 2024,
proporcionando estadísticas detalladas por mes y capacidades de filtrado.
CONFIGURADO PARA BUSCAR EN INBOX.
"""
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from outlook.graph_client import get_authenticated_session, validate_session
from outlook.mail_reader import get_messages, get_messages_by_sender
from outlook.folder_reader import get_messages_from_folder
from outlook.attachments import get_attachment_info
from utils.logger_config import setup_logger
from config import get_config_summary, validate_config

logger = setup_logger("test_correos_agosto_inbox")

def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    Convierte una cadena de fecha ISO a objeto datetime.
    
    Args:
        date_str: Fecha en formato ISO string
        
    Returns:
        datetime object o None si hay error
    """
    try:
        # Formato típico de Microsoft Graph: 2024-08-15T10:30:00Z
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
    except:
        return None

def filter_messages_by_date_range(messages: List[Dict], start_date: datetime, end_date: datetime) -> List[Dict]:
    """
    Filtra mensajes por rango de fechas.
    
    Args:
        messages: Lista de mensajes
        start_date: Fecha de inicio
        end_date: Fecha de fin
        
    Returns:
        Lista de mensajes filtrados
    """
    filtered_messages = []
    
    for message in messages:
        received_date_str = message.get("receivedDateTime")
        if not received_date_str:
            continue
            
        received_date = parse_date_string(received_date_str)
        if not received_date:
            continue
            
        if start_date <= received_date <= end_date:
            filtered_messages.append(message)
    
    return filtered_messages

def get_date_ranges_from_august() -> List[tuple]:
    """
    Genera rangos de fechas SOLO del año 2025.
    
    Returns:
        Lista de tuplas (inicio, fin, nombre_periodo)
    """
    target_year = 2025 # ⭐ CAMBIADO AL AÑO 2025
    ranges = []
    
    # Lista de todos los meses del año 2025 desde septiembre hacia atrás
    months_info = [
        (9, "Septiembre"), (8, "Agosto"), (7, "Julio"), (6, "Junio"), 
        (5, "Mayo"), (4, "Abril"), (3, "Marzo"),
        (2, "Febrero"), (1, "Enero")
    ]
    
    # Agregar TODOS los meses del 2025 desde septiembre hacia enero
    for month_num, month_name in months_info:
        # Calcular último día del mes
        if month_num == 2:
            # Febrero - verificar si es año bisiesto
            if target_year % 4 == 0 and (target_year % 100 != 0 or target_year % 400 == 0):
                last_day = 29  # Año bisiesto
            else:
                last_day = 28  # Año normal
        elif month_num in [4, 6, 9, 11]:
            last_day = 30
        else:
            last_day = 31
        
        month_start = datetime(target_year, month_num, 1)
        month_end = datetime(target_year, month_num, last_day, 23, 59, 59)
        
        ranges.append((month_start, month_end, f"{month_name} {target_year}"))
    
    # Agregar también los meses restantes del 2025 (octubre-diciembre)
    remaining_months = [
        (12, "Diciembre"), (11, "Noviembre"), (10, "Octubre")
    ]
    
    for month_num, month_name in remaining_months:
        # Calcular último día del mes
        if month_num in [4, 6, 9, 11]:
            last_day = 30
        else:
            last_day = 31
        
        month_start = datetime(target_year, month_num, 1)
        month_end = datetime(target_year, month_num, last_day, 23, 59, 59)
        ranges.append((month_start, month_end, f"{month_name} {target_year}"))
    
    # Ordenar los rangos cronológicamente (más reciente primero)
    ranges.sort(key=lambda x: x[0], reverse=True)
    
    return ranges

def analyze_messages_by_month(messages: List[Dict]) -> Dict[str, Dict]:
    """
    Analiza mensajes agrupándolos por mes.
    
    Args:
        messages: Lista de mensajes
        
    Returns:
        Diccionario con estadísticas por mes
    """
    monthly_stats = {}
    
    for message in messages:
        received_date_str = message.get("receivedDateTime")
        if not received_date_str:
            continue
            
        received_date = parse_date_string(received_date_str)
        if not received_date:
            continue
            
        month_key = received_date.strftime("%Y-%m")
        month_name = received_date.strftime("%B %Y")
        
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                "name": month_name,
                "count": 0,
                "with_attachments": 0,
                "senders": set(),
                "subjects": [],
                "messages": []
            }
        
        monthly_stats[month_key]["count"] += 1
        monthly_stats[month_key]["messages"].append(message)
        
        # Verificar adjuntos
        if message.get("hasAttachments", False):
            monthly_stats[month_key]["with_attachments"] += 1
        
        # Agregar remitente
        sender = message.get("from", {}).get("emailAddress", {}).get("address", "Desconocido")
        monthly_stats[month_key]["senders"].add(sender)
        
        # Agregar asunto
        subject = message.get("subject", "Sin asunto")
        monthly_stats[month_key]["subjects"].append(subject)
    
    # Convertir sets a listas para serialización
    for stats in monthly_stats.values():
        stats["senders"] = list(stats["senders"])
    
    return monthly_stats

def search_emails_from_august_backwards(folder_name: str = "Inbox", max_messages: int = 1000) -> bool:
    """
    Busca correos del año 2025 en una carpeta específica.
    
    Args:
        folder_name: Nombre de la carpeta a buscar (por defecto: Inbox)
        max_messages: Número máximo de mensajes a obtener
        
    Returns:
        bool: True si la búsqueda fue exitosa
    """
    target_year = 2025 # ⭐ CAMBIADO AL AÑO 2025
    logger.info(f"🔍 Buscando correos del año {target_year} en carpeta '{folder_name}'...")
    
    try:
        # Si es Inbox, usar get_messages SIN FILTROS para obtener TODOS los correos
        if folder_name.lower() == "inbox":
            logger.info(f"📧 Obteniendo TODOS los mensajes del Inbox SIN FILTROS DE REMITENTE (máximo {max_messages})...")
            logger.info("🌐 BUSCANDO CORREOS DE TODOS LOS DOMINIOS Y REMITENTES")
            messages = get_messages(top=max_messages)
        else:
            # Para otras carpetas, usar get_messages_from_folder
            logger.info(f"📧 Obteniendo mensajes de la carpeta '{folder_name}' (máximo {max_messages})...")
            messages = get_messages_from_folder(folder_name, top=max_messages)
        
        if not messages:
            logger.warning(f"⚠️ No se encontraron mensajes en '{folder_name}'")
            return False
        
        logger.info(f"✅ Se obtuvieron {len(messages)} mensajes de '{folder_name}'")
        
        # Mostrar muestra de fechas de los correos encontrados
        logger.info(f"\n📅 MUESTRA DE FECHAS DE LOS CORREOS ENCONTRADOS (primeros 10):")
        for i, msg in enumerate(messages[:10]):
            received_date_str = msg.get("receivedDateTime", "")
            subject = msg.get("subject", "Sin asunto")[:50] + "..." if len(msg.get("subject", "")) > 50 else msg.get("subject", "Sin asunto")
            sender = msg.get("from", {}).get("emailAddress", {}).get("address", "Desconocido")
            
            fecha_legible = "Fecha desconocida"
            if received_date_str:
                try:
                    fecha_obj = parse_date_string(received_date_str)
                    if fecha_obj:
                        fecha_legible = fecha_obj.strftime("%d/%m/%Y %H:%M")
                except:
                    fecha_legible = received_date_str[:16]
            
            logger.info(f"   {i+1}. 📅 {fecha_legible} | {subject} | 📧 {sender}")
        
        if len(messages) > 10:
            logger.info(f"   ... y {len(messages) - 10} correos más")
        logger.info("")
        
        # Obtener rangos de fechas
        date_ranges = get_date_ranges_from_august()
        logger.info(f"📅 Rangos de fechas generados: {len(date_ranges)}")
        for i, (start, end, name) in enumerate(date_ranges):
            logger.info(f"   {i+1}. {name}: {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}")
        
        total_filtered = 0
        results_by_period = {}
        
        # Filtrar mensajes por cada período
        for start_date, end_date, period_name in date_ranges:
            logger.info(f"\n📅 Analizando período: {period_name}")
            logger.info(f"   Desde: {start_date.strftime('%Y-%m-%d')}")
            logger.info(f"   Hasta: {end_date.strftime('%Y-%m-%d')}")
            
            period_messages = filter_messages_by_date_range(messages, start_date, end_date)
            
            if period_messages:
                logger.info(f"✅ Encontrados {len(period_messages)} mensajes en {period_name}")
                
                # Analizar mensajes del período
                with_attachments = sum(1 for msg in period_messages if msg.get("hasAttachments", False))
                senders = set()
                
                for msg in period_messages:
                    sender = msg.get("from", {}).get("emailAddress", {}).get("address", "Desconocido")
                    senders.add(sender)
                
                logger.info(f"   📎 Mensajes con adjuntos: {with_attachments}")
                logger.info(f"   👥 Remitentes únicos: {len(senders)}")
                
                # Mostrar algunos ejemplos con fechas formateadas
                logger.info(f"   📨 Ejemplos de mensajes:")
                for i, msg in enumerate(period_messages[:3]):
                    subject = msg.get("subject", "Sin asunto")
                    sender = msg.get("from", {}).get("emailAddress", {}).get("address", "Desconocido")
                    received_date_str = msg.get("receivedDateTime", "")
                    
                    # Formatear fecha para mostrar más legible
                    fecha_legible = "Fecha desconocida"
                    if received_date_str:
                        try:
                            fecha_obj = parse_date_string(received_date_str)
                            if fecha_obj:
                                fecha_legible = fecha_obj.strftime("%d/%m/%Y %H:%M")
                        except:
                            fecha_legible = received_date_str[:16]  # Fallback
                    
                    logger.info(f"      {i+1}. 📅 {fecha_legible} | '{subject}' de {sender}")
                
                if len(period_messages) > 3:
                    logger.info(f"      ... y {len(period_messages) - 3} mensajes más")
                
                results_by_period[period_name] = {
                    "count": len(period_messages),
                    "with_attachments": with_attachments,
                    "unique_senders": len(senders),
                    "messages": period_messages
                }
                
                total_filtered += len(period_messages)
            else:
                logger.info(f"📭 No se encontraron mensajes en {period_name}")
                results_by_period[period_name] = {
                    "count": 0,
                    "with_attachments": 0,
                    "unique_senders": 0,
                    "messages": []
                }
        
        # Resumen general
        logger.info(f"\n{'='*60}")
        logger.info("📊 RESUMEN DE BÚSQUEDA DEL AÑO 2025")
        logger.info(f"{'='*60}")
        logger.info(f"📁 Carpeta analizada: {folder_name}")
        logger.info(f"📧 Total mensajes obtenidos: {len(messages)}")
        logger.info(f"🎯 Mensajes del año 2025: {total_filtered}")
        
        logger.info(f"\n📅 ESTADÍSTICAS POR PERÍODO:")
        for period_name, stats in results_by_period.items():
            logger.info(f"   {period_name}: {stats['count']} mensajes ({stats['with_attachments']} con adjuntos, {stats['unique_senders']} remitentes)")
        
        # Análisis mensual detallado
        all_filtered_messages = []
        for stats in results_by_period.values():
            all_filtered_messages.extend(stats["messages"])
        
        if all_filtered_messages:
            monthly_analysis = analyze_messages_by_month(all_filtered_messages)
            
            logger.info(f"\n📈 ANÁLISIS MENSUAL DETALLADO:")
            for month_key, stats in sorted(monthly_analysis.items(), reverse=True):
                logger.info(f"   {stats['name']}: {stats['count']} mensajes")
                logger.info(f"      📎 Con adjuntos: {stats['with_attachments']}")
                logger.info(f"      👥 Remitentes únicos: {len(stats['senders'])}")
                
                # Mostrar top 3 remitentes si hay datos
                if stats['senders']:
                    top_senders = stats['senders'][:3]
                    logger.info(f"      📧 Top remitentes: {', '.join(top_senders)}")
                
                # Mostrar algunos ejemplos de mensajes con fechas del mes
                if stats['messages']:
                    logger.info(f"      📅 Ejemplos de fechas del mes:")
                    for i, msg in enumerate(stats['messages'][:3]):
                        received_date_str = msg.get("receivedDateTime", "")
                        subject = msg.get("subject", "Sin asunto")[:50] + "..." if len(msg.get("subject", "")) > 50 else msg.get("subject", "Sin asunto")
                        
                        fecha_legible = "Fecha desconocida"
                        if received_date_str:
                            try:
                                fecha_obj = parse_date_string(received_date_str)
                                if fecha_obj:
                                    fecha_legible = fecha_obj.strftime("%d/%m/%Y %H:%M")
                            except:
                                fecha_legible = received_date_str[:16]
                        
                        logger.info(f"         • {fecha_legible} - {subject}")
                    
                    if len(stats['messages']) > 3:
                        logger.info(f"         ... y {len(stats['messages']) - 3} mensajes más del mes")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error buscando correos desde agosto: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return False

def search_specific_senders_from_august(senders: List[str], folder_name: str = "Inbox") -> bool:
    """
    Busca correos de remitentes específicos del año 2025.
    
    Args:
        senders: Lista de direcciones de correo o dominios
        folder_name: Nombre de la carpeta a buscar (por defecto: Inbox)
        
    Returns:
        bool: True si la búsqueda fue exitosa
    """
    logger.info(f"🔍 Buscando correos de remitentes específicos del año 2024...")
    logger.info(f"👥 Remitentes: {', '.join(senders)}")
    logger.info(f"📁 Carpeta: {folder_name}")
    
    try:
        # Obtener mensajes por remitente
        messages = get_messages_by_sender(senders, top=500)
        
        if not messages:
            logger.warning("⚠️ No se encontraron mensajes de los remitentes especificados")
            return False
        
        logger.info(f"✅ Se obtuvieron {len(messages)} mensajes de los remitentes especificados")
        
        # Filtrar SOLO del año 2025 completo
        target_year = 2025 # ⭐ CAMBIADO AL AÑO 2025
        year_start = datetime(target_year, 1, 1)  # 1 enero 2025
        year_end = datetime(target_year, 12, 31, 23, 59, 59)  # 31 diciembre 2025
        
        filtered_messages = filter_messages_by_date_range(messages, year_start, year_end)
        
        if filtered_messages:
            logger.info(f"📅 Mensajes del año {target_year}: {len(filtered_messages)}")
            
            # Análisis por remitente
            sender_stats = {}
            for message in filtered_messages:
                sender = message.get("from", {}).get("emailAddress", {}).get("address", "Desconocido")
                
                if sender not in sender_stats:
                    sender_stats[sender] = {
                        "count": 0,
                        "with_attachments": 0,
                        "subjects": []
                    }
                
                sender_stats[sender]["count"] += 1
                if message.get("hasAttachments", False):
                    sender_stats[sender]["with_attachments"] += 1
                
                subject = message.get("subject", "Sin asunto")
                sender_stats[sender]["subjects"].append(subject)
            
            # Mostrar estadísticas por remitente
            logger.info(f"\n📊 ESTADÍSTICAS POR REMITENTE:")
            for sender, stats in sender_stats.items():
                logger.info(f"   📧 {sender}: {stats['count']} mensajes ({stats['with_attachments']} con adjuntos)")
                
                # Mostrar algunos mensajes con fechas
                logger.info(f"      📅 Ejemplos con fechas:")
                mensajes_con_fechas = [(msg.get("receivedDateTime", ""), msg.get("subject", "Sin asunto")) 
                                     for msg in filtered_messages if msg.get("from", {}).get("emailAddress", {}).get("address", "") == sender]
                
                for i, (fecha_str, subject) in enumerate(mensajes_con_fechas[:3]):
                    fecha_legible = "Fecha desconocida"
                    if fecha_str:
                        try:
                            fecha_obj = parse_date_string(fecha_str)
                            if fecha_obj:
                                fecha_legible = fecha_obj.strftime("%d/%m/%Y %H:%M")
                        except:
                            fecha_legible = fecha_str[:16]
                    
                    subject_corto = subject[:50] + "..." if len(subject) > 50 else subject
                    logger.info(f"         • {fecha_legible} - {subject_corto}")
                
                if len(mensajes_con_fechas) > 3:
                    logger.info(f"         ... y {len(mensajes_con_fechas) - 3} mensajes más de este remitente")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error buscando correos por remitente: {e}")
        return False

def test_august_search() -> bool:
    """
    Prueba principal para buscar correos del año 2025.
    
    Returns:
        bool: True si todas las pruebas pasan
    """
    logger.info("🧪 Iniciando pruebas de búsqueda del año 2025...")
    
    try:
        # Validar configuración
        logger.info("🔧 Validando configuración...")
        validate_config()
        logger.info("✅ Configuración válida")
        
        # Validar autenticación
        logger.info("🔐 Validando autenticación...")
        session = get_authenticated_session()
        if not validate_session(session):
            logger.error("❌ Sesión no válida")
            return False
        logger.info("✅ Autenticación exitosa")
        
        # Buscar correos en Inbox
        logger.info("\n" + "="*60)
        logger.info("📧 BÚSQUEDA EN CARPETA INBOX")
        logger.info("="*60)
        
        logger.info("🚀 Iniciando search_emails_from_august_backwards...")
        success1 = search_emails_from_august_backwards("Inbox", max_messages=2000)
        logger.info(f"🔚 search_emails_from_august_backwards completado: {success1}")
        
        # Buscar correos de TODOS los remitentes (sin restricciones)
        logger.info("\n" + "="*60)
        logger.info("👥 BÚSQUEDA DE TODOS LOS REMITENTES")
        logger.info("="*60)
        
        logger.info("🌐 Analizando correos de TODOS los dominios sin restricciones...")
        
        # Ya hemos obtenido todos los mensajes en success1, no necesitamos una segunda búsqueda restrictiva
        # Simplemente reportamos que hemos analizado todos los remitentes
        success2 = True
        logger.info("✅ Análisis de todos los remitentes completado en la búsqueda principal")
        
        return success1 and success2
        
    except Exception as e:
        logger.error(f"❌ Error en pruebas de búsqueda: {e}")
        return False

def main():
    """
    Función principal del script de pruebas de búsqueda del año 2025.
    """
    target_year = 2025 # ⭐ CAMBIADO AL AÑO 2025
    logger.info(f"🔍 BÚSQUEDA DE CORREOS DEL AÑO {target_year}")
    logger.info("📧 BUSCANDO EN INBOX")
    logger.info("=" * 60)
    
    try:
        # Ejecutar pruebas de búsqueda
        start_time = time.time()
        success = test_august_search()
        end_time = time.time()
        
        duration = f"{end_time - start_time:.2f}s"
        
        if success:
            logger.info(f"\n✅ Búsqueda completada exitosamente en {duration}")
            logger.info("🎉 ¡Todos los datos fueron obtenidos correctamente!")
            sys.exit(0)
        else:
            logger.error(f"\n❌ La búsqueda falló en {duration}")
            logger.error("⚠️ Revisa los logs para más detalles")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Búsqueda interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ Error inesperado durante la búsqueda: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
