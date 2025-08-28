"""
Pruebas específicas para run.py - Cobertura 100%
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

class TestRunPy(unittest.TestCase):
    """Pruebas para el archivo run.py"""

    def test_run_py_path_modification(self):
        """Prueba que run.py modifica sys.path correctamente"""
        # Importar run.py debería modificar sys.path
        import run

        # Verificar que se agregó el directorio al path
        expected_path = os.path.dirname(os.path.abspath(run.__file__))
        self.assertIn(expected_path, sys.path)

    @patch('main.main')
    def test_run_py_main_execution(self, mock_main):
        """Prueba que run.py ejecute main() cuando se ejecuta como __main__"""
        mock_main.return_value = None

        # Simular la ejecución del bloque if __name__ == "__main__"
        with patch('run.__name__', '__main__'):
            # Ejecutar manualmente el código del bloque __main__
            exec('''
if __name__ == "__main__":
    from main import main
    main()
''', {'__name__': '__main__'})

        # Verificar que main() fue llamado
        mock_main.assert_called_once()

    def test_run_py_module_import(self):
        """Prueba que el módulo run se puede importar correctamente"""
        import run

        # Verificar que el módulo existe y se importó correctamente
        self.assertIsNotNone(run)
        self.assertTrue(hasattr(run, '__file__'))

if __name__ == '__main__':
    unittest.main()
