"""
Módulo de Scraping - Reutilizable para cualquier robot
"""
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# Agregar el directorio padre al path para importar el framework
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from framework.modules.base_module import BaseModule

logger = logging.getLogger(__name__)

class ScrapingModule(BaseModule):
    """Módulo de scraping reutilizable para cualquier robot"""
    
    def __init__(self, module_id: str, robot_id: str, config: Dict[str, Any] = None):
        default_config = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'timeout': 30,
            'max_retries': 3,
            'delay_between_requests': 1.0,
            'follow_redirects': True,
            'verify_ssl': True
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(module_id, robot_id, default_config)
        self.session = None
        self.scraped_data = []
    
    async def _initialize_module(self):
        """Inicialización específica del módulo de scraping"""
        logger.info("Inicializando módulo de scraping")
        
        # Crear sesión HTTP
        timeout = aiohttp.ClientTimeout(total=self.config['timeout'])
        connector = aiohttp.TCPConnector(verify_ssl=self.config['verify_ssl'])
        
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': self.config['user_agent']},
            timeout=timeout,
            connector=connector
        )
        
        logger.info("Módulo de scraping inicializado correctamente")
    
    async def _execute_module(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar scraping según los parámetros"""
        try:
            url = params.get('url')
            selectors = params.get('selectors', {})
            max_pages = params.get('max_pages', 1)
            delay = params.get('delay', self.config['delay_between_requests'])
            
            if not url:
                raise ValueError("URL es requerida para el scraping")
            
            logger.info(f"Iniciando scraping de: {url}")
            
            # Realizar scraping
            scraped_data = await self._scrape_url(url, selectors, max_pages, delay)
            
            # Guardar datos en base de datos
            await self._save_scraped_data(scraped_data, params)
            
            return {
                'success': True,
                'url': url,
                'data_count': len(scraped_data),
                'data': scraped_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en scraping: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _scrape_url(self, url: str, selectors: Dict[str, str], max_pages: int = 1, delay: float = 1.0) -> List[Dict[str, Any]]:
        """Realizar scraping de una URL"""
        scraped_data = []
        
        try:
            for page in range(1, max_pages + 1):
                page_url = url
                if page > 1:
                    # Agregar parámetro de página si es necesario
                    separator = '&' if '?' in url else '?'
                    page_url = f"{url}{separator}page={page}"
                
                logger.info(f"Scraping página {page}: {page_url}")
                
                # Realizar request
                async with self.session.get(page_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        page_data = await self._parse_html(html_content, selectors, page_url)
                        scraped_data.extend(page_data)
                        
                        logger.info(f"Página {page}: {len(page_data)} elementos encontrados")
                    else:
                        logger.warning(f"Error HTTP {response.status} para página {page}")
                
                # Esperar entre páginas
                if page < max_pages:
                    await asyncio.sleep(delay)
        
        except Exception as e:
            logger.error(f"Error al hacer scraping de {url}: {e}")
        
        return scraped_data
    
    async def _parse_html(self, html_content: str, selectors: Dict[str, str], source_url: str) -> List[Dict[str, Any]]:
        """Parsear HTML usando selectores CSS"""
        parsed_data = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Si no hay selectores específicos, extraer información básica
            if not selectors:
                # Extraer todos los enlaces
                links = soup.find_all('a', href=True)
                for link in links:
                    parsed_data.append({
                        'type': 'link',
                        'text': link.get_text(strip=True),
                        'url': link['href'],
                        'source_url': source_url,
                        'scraped_at': datetime.now().isoformat()
                    })
                
                # Extraer títulos
                titles = soup.find_all(['h1', 'h2', 'h3'])
                for title in titles:
                    parsed_data.append({
                        'type': 'title',
                        'text': title.get_text(strip=True),
                        'tag': title.name,
                        'source_url': source_url,
                        'scraped_at': datetime.now().isoformat()
                    })
            else:
                # Usar selectores específicos
                for key, selector in selectors.items():
                    elements = soup.select(selector)
                    for element in elements:
                        parsed_data.append({
                            'type': key,
                            'text': element.get_text(strip=True),
                            'html': str(element),
                            'selector': selector,
                            'source_url': source_url,
                            'scraped_at': datetime.now().isoformat()
                        })
        
        except Exception as e:
            logger.error(f"Error al parsear HTML: {e}")
        
        return parsed_data
    
    async def _save_scraped_data(self, scraped_data: List[Dict[str, Any]], params: Dict[str, Any]):
        """Guardar datos scraped en la base de datos"""
        try:
            for data in scraped_data:
                # Crear caso de transacción para cada dato
                case_data = {
                    'case_id': f"scraping_{hash(str(data))}",
                    'transaction_type': 'web_scraping',
                    'status': 'completed',
                    'data': data,
                    'priority': 1,
                    'assigned_to': self.module_id,
                    'notes': f"Dato scraped de {params.get('url', 'URL desconocida')}"
                }
                
                # Insertar en base de datos
                success = await self.db_manager.insert_case_transaction(
                    self.robot_id, case_data
                )
                
                if success:
                    self.scraped_data.append(data)
                    logger.debug(f"Dato guardado: {data.get('text', '')[:50]}...")
                else:
                    logger.warning(f"No se pudo guardar dato: {data.get('text', '')[:50]}...")
        
        except Exception as e:
            logger.error(f"Error al guardar datos scraped: {e}")
    
    async def _cleanup(self):
        """Limpieza de recursos específicos del módulo"""
        if self.session:
            await self.session.close()
            logger.info("Sesión HTTP cerrada")
    
    async def get_scraping_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del scraping"""
        return {
            'total_data_scraped': len(self.scraped_data),
            'module_id': self.module_id,
            'robot_id': self.robot_id,
            'scraped_data': self.scraped_data[-10:]  # Últimos 10 datos como muestra
        }
