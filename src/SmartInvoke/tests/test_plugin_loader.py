import pytest
from unittest.mock import patch, MagicMock
from common.plugin_loader import PluginLoader  # Replace 'common.plugin_loader' with the actual module name

@pytest.fixture
def mock_import_module():
    with patch('common.plugin_loader.importlib.import_module') as mock_import:
        yield mock_import

def test_load_class_success(mock_import_module):
    mock_module = MagicMock()
    mock_class = MagicMock()
    mock_import_module.return_value = mock_module
    setattr(mock_module, 'TestClass', mock_class)

    loaded_class = PluginLoader.load_class('test_module', 'TestClass')
    mock_import_module.assert_called_with('test_module')
    assert loaded_class == mock_class

def test_load_class_attribute_error(mock_import_module):
    mock_module = MagicMock()
    mock_import_module.return_value = mock_module
    delattr(mock_module, 'NonExistentClass')

    with pytest.raises(AttributeError):
        PluginLoader.load_class('test_module', 'NonExistentClass')

def test_load_class_import_error(mock_import_module):
    mock_import_module.side_effect = ImportError

    with pytest.raises(ImportError):
        PluginLoader.load_class('non_existent_module', 'TestClass')