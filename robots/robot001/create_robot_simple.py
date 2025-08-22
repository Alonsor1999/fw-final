"""
Versión simplificada para crear un robot
"""
import requests
import json

def create_simple_robot():
    """Crear robot con configuración mínima"""
    
    url = "http://localhost:8000/api/v1/robots/"
    
    # Datos mínimos del robot
    robot_data = {
        "robot_name": "Robot Simple Test",
        "description": "Robot de prueba simple",
        "robot_type": "web_scraping",
        "config_data": {"test": True},  # Configuración mínima
        "tags": []
    }
    
    try:
        print("Enviando datos:", json.dumps(robot_data, indent=2))
        response = requests.post(url, json=robot_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Robot creado exitosamente!")
            print(f"📋 Robot ID: {result.get('robot_id', 'N/A')}")
            print(f"📊 Status: {result.get('status', 'N/A')}")
            print(f"🔧 Module: {result.get('module', 'N/A')}")
            return result.get('robot_id')
        else:
            print("❌ Error creando robot")
            return None
            
    except Exception as e:
        print(f"❌ Error en la petición: {e}")
        return None

if __name__ == "__main__":
    create_simple_robot()
