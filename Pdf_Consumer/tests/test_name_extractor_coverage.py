"""
Pruebas unitarias adicionales para mejorar cobertura de name_extractor.py
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestNameExtractorCoverage(unittest.TestCase):
    """Pruebas adicionales para mejorar cobertura de name_extractor"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        try:
            from extractors.name_extractor import NameExtractor
            self.extractor = NameExtractor()
            self.available = True
        except ImportError:
            self.available = False

    def test_norm_phrase_unicode_handling(self):
        """Prueba _norm_phrase con manejo de unicode"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Test normalización unicode
        text_with_accents = "José María Ñoño"
        result = self.extractor._norm_phrase(text_with_accents)
        self.assertIsInstance(result, str)
        self.assertEqual(result.lower(), result)  # Debe estar en minúsculas

    def test_contains_blacklisted_phrase_regex(self):
        """Prueba _contains_blacklisted_phrase con regex y frases prohibidas"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Mock BLACKLIST_PHRASES y BLACKLIST_REGEXES para testing específico
        with patch('extractors.name_extractor.BLACKLIST_PHRASES', {'juan prohibido'}):
            result = self.extractor._contains_blacklisted_phrase("Juan Prohibido")
            self.assertTrue(result)

        # Test caso donde no está en blacklist
        result = self.extractor._contains_blacklisted_phrase("Juan Carlos Pérez")
        # El resultado puede variar según la configuración real

    def test_smart_title_with_connectors(self):
        """Prueba smart_title con conectores especiales"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Mock CONNECTORS para prueba específica
        with patch('extractors.name_extractor.CONNECTORS', {'de', 'la', 'del'}):
            result = self.extractor.smart_title("juan de la cruz")
            self.assertIn("Juan", result)
            self.assertIn("de", result)  # Los conectores no deben capitalizarse

    def test_clean_name_frag_edge_cases(self):
        """Prueba clean_name_frag con casos edge"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Test con None
        result = self.extractor.clean_name_frag(None)
        self.assertEqual(result, "")

        # Test con texto que contiene patrones específicos
        text_with_qepd = "Juan Pérez (q.e.p.d.)"
        result = self.extractor.clean_name_frag(text_with_qepd)
        self.assertNotIn("q.e.p.d", result)

        # Test con múltiples signos de puntuación
        text_with_punct = "Juan,,,Pérez;;;Carlos:::"
        result = self.extractor.clean_name_frag(text_with_punct)
        self.assertNotIn(",,", result)

    def test_plausible_person_edge_cases(self):
        """Prueba plausible_person con casos edge específicos"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Test con un solo token
        result = self.extractor.plausible_person("Juan")
        self.assertFalse(result)

        # Test con conectores al inicio y final
        with patch('extractors.name_extractor.CONNECTORS', {'de', 'la'}):
            result = self.extractor.plausible_person("de Juan Pérez")
            self.assertFalse(result)
            
            result = self.extractor.plausible_person("Juan Pérez de")
            self.assertFalse(result)

        # Test con tokens que contienen ruido institucional
        with patch('extractors.name_extractor.INSTITUTION_NOISE', {'UNIVERSIDAD', 'GOBIERNO'}):
            result = self.extractor.plausible_person("Juan Universidad")
            self.assertFalse(result)

    def test_tokens_from_value_edge_cases(self):
        """Prueba _tokens_from_value con casos edge"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Test con None
        result = self.extractor._tokens_from_value(None)
        self.assertIsInstance(result, list)

        # Test con caracteres especiales unicode
        text_with_unicode = "Juan\u00A0Carlos\u200BPérez"
        result = self.extractor._tokens_from_value(text_with_unicode)
        self.assertIsInstance(result, list)

        # Test con valores "NINGUNA" y "NINGUNO"
        text_with_ninguna = "Juan NINGUNA NINGUNO Carlos"
        result = self.extractor._tokens_from_value(text_with_ninguna)
        self.assertNotIn("NINGUNA", result)
        self.assertNotIn("NINGUNO", result)

    def test_extract_by_field_lines_robusto_edge_cases(self):
        """Prueba _extract_by_field_lines_robusto con casos edge"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Test con texto que tiene líneas de campo válidas
        text_with_fields = """Primer Nombre: Juan Carlos
Segundo Nombre: José
Primer Apellido: Pérez
Segundo Apellido: González
Alguna otra línea
Primer Nombre: María
Primer Apellido: López"""
        
        result = self.extractor._extract_by_field_lines_robusto(text_with_fields)
        self.assertIsInstance(result, list)

        # Test con líneas que necesitan lookahead
        text_with_lookahead = """Primer Nombre:
Juan Carlos
Primer Apellido: Pérez"""
        
        result = self.extractor._extract_by_field_lines_robusto(text_with_lookahead)
        self.assertIsInstance(result, list)

    def test_is_authority_context(self):
        """Prueba _is_authority_context"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Mock PRE_CONTEXT_AUTH para prueba específica
        with patch('extractors.name_extractor.PRE_CONTEXT_AUTH') as mock_auth:
            mock_auth.search.return_value = True
            result = self.extractor._is_authority_context("texto con autoridad Juan Pérez", 50)
            self.assertTrue(result)

            mock_auth.search.return_value = None
            result = self.extractor._is_authority_context("texto normal Juan Pérez", 20)
            self.assertFalse(result)

    def test_extract_blocks_after_numbers(self):
        """Prueba _extract_blocks_after_numbers con casos específicos"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Text con números seguidos de bloques de nombres
        text_with_numbers = """1. Información general
JUAN
CARLOS
PÉREZ
GONZÁLEZ
2. Otra sección
MARÍA
LÓPEZ
SANTOS
3. Final"""

        result = self.extractor._extract_blocks_after_numbers(text_with_numbers)
        self.assertIsInstance(result, list)

        # Test con bloques que no cumplen criterios (muy pocos o muchos tokens)
        text_insufficient = """1. Sección
JUAN
2. Otra"""
        
        result = self.extractor._extract_blocks_after_numbers(text_insufficient)
        self.assertIsInstance(result, list)

    def test_extract_generic_anywhere_filtering(self):
        """Prueba _extract_generic_anywhere con diferentes filtros"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Test con contexto bloqueado
        with patch('extractors.name_extractor.PRE_CONTEXT_BLOCK') as mock_block:
            mock_block.search.return_value = True
            result = self.extractor._extract_generic_anywhere("Juan Carlos Pérez")
            self.assertIsInstance(result, list)

        # Test con tokens que terminan en "ando" o "endo"
        text_with_gerund = "Juan Estudiando Carlos Corriendo"
        result = self.extractor._extract_generic_anywhere(text_with_gerund)
        self.assertIsInstance(result, list)

        # Test con blacklisted tokens
        with patch('extractors.name_extractor.BLACKLIST_TOKENS', {'JUAN', 'PROHIBIDO'}):
            result = self.extractor._extract_generic_anywhere("Juan Prohibido Carlos")
            self.assertIsInstance(result, list)

    def test_extract_by_phrase_patterns(self):
        """Prueba _extract_by_phrase_patterns"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Mock uno de los patrones para testing
        mock_pattern = MagicMock()
        mock_match = MagicMock()
        mock_match.start.return_value = 10
        mock_match.group.return_value = "Juan Carlos Pérez"
        mock_pattern.finditer.return_value = [mock_match]

        with patch('extractors.name_extractor.RE_MAYOR_IDENT', mock_pattern):
            result = self.extractor._extract_by_phrase_patterns("Texto con nombre Juan Carlos Pérez")
            self.assertIsInstance(result, list)

    def test_extract_all_names_comprehensive(self):
        """Prueba extract_all_names con flujo completo"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Test con texto que debería activar múltiples extractores
        comprehensive_text = """
        Primer Nombre: Juan Carlos
        Primer Apellido: Pérez
        
        El señor María López presenta esta demanda.
        
        1. Accionante
        PEDRO
        GONZÁLEZ
        SANTOS
        
        Contra los herederos de Ana Ruiz.
        """

        result = self.extractor.extract_all_names(comprehensive_text)
        self.assertIsInstance(result, str)

        # Test con texto vacío
        result = self.extractor.extract_all_names("")
        self.assertEqual(result, "")

        # Test con None
        result = self.extractor.extract_all_names(None)
        self.assertEqual(result, "")

    def test_extract_names_with_pages_method(self):
        """Prueba extract_names_with_pages si existe"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Verificar si el método existe
        if hasattr(self.extractor, 'extract_names_with_pages'):
            pages_text = [("Juan Carlos Pérez vive aquí", 1), ("María López trabaja", 2)]
            result = self.extractor.extract_names_with_pages(pages_text)
            self.assertIsInstance(result, list)

    def test_internal_push_function_edge_cases(self):
        """Prueba casos edge de la función interna _push en extract_all_names"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Test con nombres que no son plausibles
        text_with_implausible = "texto X Y Z final"
        result = self.extractor.extract_all_names(text_with_implausible)
        self.assertIsInstance(result, str)

        # Test con nombres duplicados en diferentes posiciones
        text_with_duplicates = "Juan Pérez trabaja aquí. Más tarde Juan Pérez regresó."
        result = self.extractor.extract_all_names(text_with_duplicates)
        self.assertIsInstance(result, str)
        # Los duplicados deberían eliminarse

    def test_patterns_with_authority_context(self):
        """Prueba patrones que son filtrados por contexto de autoridad"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Mock authority context para que siempre retorne True
        with patch.object(self.extractor, '_is_authority_context', return_value=True):
            # Este texto debería ser filtrado por contexto de autoridad
            text_authority = "El juez Juan Carlos Pérez dictaminó"
            result = self.extractor.extract_all_names(text_authority)
            self.assertIsInstance(result, str)

    def test_fallback_position_calculation(self):
        """Prueba cálculo de posiciones para nombres de fallback"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Test con nombres que no se encuentran en el texto original
        # (esto activa las posiciones de fallback con 10**9 + idx)
        text_fields_only = """
        Primer Nombre: Inventado
        Primer Apellido: NoExiste
        """
        result = self.extractor.extract_all_names(text_fields_only)
        self.assertIsInstance(result, str)

    def test_complex_field_parsing_edge_cases(self):
        """Prueba casos edge complejos en parsing de campos"""
        if not self.available:
            self.skipTest("NameExtractor not available")

        # Test con campos incompletos
        incomplete_fields = """
        Primer Nombre: Juan
        Segundo Apellido: 
        Primer Apellido: Pérez
        """
        result = self.extractor._extract_by_field_lines_robusto(incomplete_fields)
        self.assertIsInstance(result, list)

        # Test donde el siguiente campo fuerza flush
        forcing_flush = """
        Primer Nombre: Juan
        Primer Apellido: Pérez
        Primer Nombre: María
        """
        result = self.extractor._extract_by_field_lines_robusto(forcing_flush)
        self.assertIsInstance(result, list)

if __name__ == '__main__':
    unittest.main()
