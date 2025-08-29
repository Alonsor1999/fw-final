#!/usr/bin/env python3
"""
Script para visualizar los resultados de las capas de procesamiento del Robot001
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

def view_layer_results():
    """Visualizar resultados de las capas de procesamiento"""
    print("🔍 VISUALIZADOR DE RESULTADOS DE LAS CAPAS")
    print("=" * 60)
    
    # 1. Verificar base de datos
    db_path = Path("storage/documents.db")
    if db_path.exists():
        print(f"📊 Base de datos encontrada: {db_path}")
        view_database_results(db_path)
    else:
        print("❌ No se encontró base de datos")
    
    # 2. Verificar logs
    print(f"\n📋 REVISANDO LOGS...")
    view_log_results()
    
    # 3. Verificar archivos descargados
    print(f"\n📁 ARCHIVOS DESCARGADOS:")
    view_downloaded_files()

def view_database_results(db_path):
    """Ver resultados en la base de datos"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ver tablas disponibles
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 Tablas en la base de datos: {[table[0] for table in tables]}")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📊 {table_name}: {count} registros")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                print(f"   📄 Primeros 3 registros:")
                for i, row in enumerate(rows, 1):
                    print(f"      {i}. {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {e}")

def view_log_results():
    """Ver resultados en los logs"""
    log_path = Path("../Mail_loop_tracking/logs")
    
    if log_path.exists():
        # Buscar logs recientes
        log_files = list(log_path.glob("*.log"))
        
        for log_file in log_files:
            if log_file.name != "error.log" and log_file.name != "critical.log":
                print(f"📋 {log_file.name}:")
                
                # Buscar líneas relacionadas con capas
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    # Buscar líneas de capas
                    layer_lines = [line for line in lines if any(keyword in line for keyword in 
                        ["Capa 1", "Capa 2", "Capa 3", "Capa 4", "Capa 5", "RESULTADOS DETALLADOS"])]
                    
                    if layer_lines:
                        print(f"   🔍 Encontradas {len(layer_lines)} líneas de capas:")
                        for line in layer_lines[-5:]:  # Últimas 5 líneas
                            print(f"      {line.strip()}")
                    else:
                        print(f"   ⚠️ No se encontraron líneas de capas")
                        
                except Exception as e:
                    print(f"   ❌ Error leyendo log: {e}")
    else:
        print("❌ No se encontró directorio de logs")

def view_downloaded_files():
    """Ver archivos descargados"""
    attachments_path = Path("robot001_attachments")
    
    if attachments_path.exists():
        files = list(attachments_path.glob("*"))
        
        if files:
            print(f"📄 Archivos descargados ({len(files)}):")
            for file in files:
                size = file.stat().st_size
                modified = datetime.fromtimestamp(file.stat().st_mtime)
                print(f"   📎 {file.name} ({size} bytes, {modified.strftime('%H:%M:%S')})")
        else:
            print("   ⚠️ No hay archivos descargados")
    else:
        print("❌ No se encontró directorio de adjuntos")

if __name__ == "__main__":
    view_layer_results()
