import pytest
from common.context import Context 

@pytest.fixture
def context():
    return Context()

def test_set_and_get(context):
    context.set('key1', 'value1')
    assert context.get('key1') == 'value1'

def test_get_non_existent_key(context):
    assert context.get('non_existent_key') == ''

def test_get_with_empty_data(context):
    assert context.get('key1') == ''

def test_iter(context):
    context.set('key1', 'value1')
    context.set('key2', 'value2')
    items = list(context)
    assert ('key1', 'value1') in items
    assert ('key2', 'value2') in items

def test_set_overwrite(context):
    context.set('key1', 'value1')
    context.set('key1', 'value2')
    assert context.get('key1') == 'value2'