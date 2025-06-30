import pytest

from services.streaming_recipe_parser.xml_tag_tracker import XMLTagTracker

def _get_results(tracker, tokens):
    results = []
    for token in tokens:
        result = tracker.track(*token)
        if result:
            if isinstance(result, list):
                results.extend(result)
            else:
                results.append(result)
    return results

@pytest.fixture()
def tracker():
    return XMLTagTracker(known_tags=['a', 'b', 'c', 'd', 'e'])


def test_track_single_start_tag(tracker):
    tokens = [
        ('start', 'a', None, '<a>'),
    ]
    
    assert _get_results(tracker, tokens) == []
    assert tracker.stack == [{'tag': 'a', 'buffer': '<a>'}]
    
    
def test_track_complete_tag(tracker):
    tokens = [
        ('start', 'a', None, '<a>'),
        ('text', None, 'hello', 'hello'),
        ('end', 'a', None, '</a>'),
    ]
    
    assert _get_results(tracker, tokens) == [('a', '<a>hello</a>')]
    assert tracker.stack == []


def test_multiple_sibling_tags(tracker):
    tokens = [
        ('start', 'a', None, '<a>'),
        ('end', 'a', None, '</a>'),
        ('start', 'b', None, '<b>'),
        ('end', 'b', None, '</b>'),
    ]
    
    assert _get_results(tracker, tokens) == [('a', '<a></a>'), ('b', '<b></b>')]
    assert tracker.stack == []
    
    
def test_text_between_tags(tracker):
    tokens = [
        ('start', 'a', None, '<a>'),
        ('text', None, 'foo', 'foo'),
        ('end', 'a', None, '</a>'),
        ('text', None, 'bar', 'bar'),
        ('start', 'b', None, '<b>'),
        ('text', None, 'baz', 'baz'),
        ('end', 'b', None, '</b>'),
    ]
    assert _get_results(tracker, tokens) == [('a', '<a>foo</a>'), ('b', '<b>baz</b>')]
    assert tracker.stack == []


def test_deep_nesting(tracker):
    tokens = [
        ('start', 'a', None, '<a>'),
        ('start', 'b', None, '<b>'),
        ('start', 'c', None, '<c>'),
        ('text', None, 'deep', 'deep'),
        ('end', 'c', None, '</c>'),
        ('end', 'b', None, '</b>'),
        ('end', 'a', None, '</a>'),
    ]
    assert _get_results(tracker, tokens) == [('c', '<c>deep</c>'), ('b', '<b><c>deep</c></b>'), ('a', '<a><b><c>deep</c></b></a>')]
    assert tracker.stack == []
    
    
def test_track_nested_open_tags(tracker):
    tokens = [
        ('start', 'a', None, '<a>'),
        ('start', 'b', None, '<b>'),
    ]
    
    assert _get_results(tracker, tokens) == []
    assert tracker.stack == [{'tag': 'a', 'buffer': '<a>'}, {'tag': 'b', 'buffer': '<b>'}]
    
    
def test_track_nested_tags_with_complete_child_tag(tracker):
    tokens = [
        ('start', 'a', None, '<a>'),
        ('start', 'b', None, '<b>'),
        ('text', None, 'hello', 'hello'),
        ('end', 'b', None, '</b>'),
    ]
    
    assert _get_results(tracker, tokens) == [('b', '<b>hello</b>')]
    assert tracker.stack == [{'tag': 'a', 'buffer': '<a><b>hello</b>'}]


def test_nested_tags(tracker):
    tokens = [
        ('start', 'a', None, '<a>'),
        ('start', 'b', None, '<b>'),
        ('text', None, 'x', 'x'),
        ('end', 'b', None, '</b>'),
        ('end', 'a', None, '</a>'),
    ]
    
    assert _get_results(tracker, tokens) == [('b', '<b>x</b>'), ('a', '<a><b>x</b></a>')]
    assert tracker.stack == []


def test_unclosed_child_tag_with_closed_parent_tag(tracker):
    tokens = [
        ('start', 'a', None, '<a>'),
        ('start', 'b', None, '<b>'),
        ('text', None, 'y', 'y'),
        ('end', 'a', None, '</a>'),
    ]
    
    assert _get_results(tracker, tokens) == [('b', '<b>y</b>'), ('a', '<a><b>y</b></a>')]
    assert tracker.stack == []
    
    
def test_nested_unclosed_child_tag_with_closed_parent_tag(tracker):
    tokens = [
        ('start', 'a', None, '<a>'),
        ('start', 'b', None, '<b>'),
        ('start', 'c', None, '<c>'),
        ('text', None, 'y', 'y'),
        ('end', 'c', None, '</c>'),
        ('end', 'a', None, '</a>'),
    ]
    
    assert _get_results(tracker, tokens) == [('c', '<c>y</c>'), ('b', '<b><c>y</c></b>'), ('a', '<a><b><c>y</c></b></a>')]
    assert tracker.stack == []  


def test_orphan_end_tag(tracker):
    tokens = [
        ('start', 'a', None, '<a>'),
        ('start', 'b', None, '<b>'),
        ('end', 'c', None, '</c>'),  # orphan end tag
        ('end', 'b', None, '</b>'),
        ('end', 'a', None, '</a>'),
    ]
    assert _get_results(tracker, tokens) == [('b', '<b></b>'), ('a', '<a><b></b></a>')]
    assert tracker.stack == []
