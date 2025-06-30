import pytest
from src.services.streaming_recipe_parser.xml_chunk_patcher import XMLChunkPatcher

def test_patch_complete_chunk():
    patcher = XMLChunkPatcher()
    assert patcher.patch('<name>Test Recipe</name>') == '<name>Test Recipe</name>'
    

def test_patch_broken_open_tags():
    patcher = XMLChunkPatcher()
    assert patcher.patch('<name') == None
    assert patcher.patch('>Test Recipe</name>') == '<name>Test Recipe</name>'
    
    assert patcher.flush() == ''
    
    assert patcher.patch('<rec') == None
    assert patcher.patch('ipe>') == '<recipe>'
    assert patcher.patch('<na') == None
    assert patcher.patch('me>Test</name>') == '<name>Test</name>'
    
    assert patcher.flush() == ''
    assert patcher.patch('Recipe <na') == 'Recipe '
    assert patcher.patch('me>Test</name>') == '<name>Test</name>'


def test_patch_chunk_ends_with_partial_open_tag():
    patcher = XMLChunkPatcher()
    assert patcher.patch('<recipe><na') == '<recipe>'
    assert patcher.patch('me>Test</name>') == '<name>Test</name>'
       
            
def test_patch_chunk_ends_with_partial_close_tag():
    patcher = XMLChunkPatcher()
    assert patcher.patch('<rec') == None
    assert patcher.patch('ipe><name') == '<recipe>'
    assert patcher.patch('>Test</name') ==  "<name>Test"
    assert patcher.patch('>') == '</name>'
    
    
def test_flush_empty_after_complete_chunk():
    patcher = XMLChunkPatcher()
    patcher.patch('<name>Test Recipe</name>')
    assert patcher.flush() == ''
    
    
def test_flush_buffer_after_incomplete_chunk():
    patcher = XMLChunkPatcher()
    patcher.patch('<na')
    assert patcher.flush() == '<na'
