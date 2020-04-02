import collections
import functools
import itertools
import re

import logging
log = logging.getLogger(__name__)


def parse_tag_regexs(_tag_regexs):
    """
    """
    assert isinstance(_tag_regexs, dict)
    return {
        tag: re.compile(tag_regex) if isinstance(tag_regex, str) else tag_regex
        for tag, tag_regex in _tag_regexs.items()
    }


def find_tags_in_string(_tag_regexs, value):
    r"""
    >>> _tag_regexs = {
    ...     'abc': '^ABC\\d+$$',
    ...     'xyz': '^XYZ\\d+$$',
    ...     'three_didget': '\\D\\d{3}$',
    ...     'four_didget': '\\D\\d{4}$',
    ... }
    >>> find_tags_in_string = functools.partial(find_tags_in_string, parse_tag_regexs(_tag_regexs))
    >>> assert find_tags_in_string('ABC123') == frozenset({'abc', 'three_didget'})
    >>> assert find_tags_in_string('ABC12') == frozenset({'abc'})
    >>> assert find_tags_in_string('DEF12') == frozenset()
    >>> assert find_tags_in_string('XYZ1234') == frozenset({'four_didget', 'xyz'})
    """
    return frozenset(filter(None, (
        tag if tag_regex.search(value) else None
        for tag, tag_regex in _tag_regexs.items()
    )))


def _reducer_parse_single_criteria(accumulator_dict, name_criteria_pair):
    """
    >>> assert _reducer_parse_single_criteria({}, ('name', ('a', 'b', ('c', 'd')))) == {frozenset({'b', 'c', 'a'}): 'name', frozenset({'b', 'd', 'a'}): 'name'}
    """
    name, criteria = name_criteria_pair
    def _split_criteria(acc, item):
        acc['tag' if isinstance(item, str) else 'tag_seq'].add(item)
        return acc
    criteria = functools.reduce(_split_criteria, criteria, collections.defaultdict(set))
    _combinations = {frozenset(criteria.get('tag', ())),}
    for group in criteria.get('tag_seq', ()):
        _current_combinations = frozenset(_combinations)
        _combinations.clear()
        for item in group:
            for existing_combination in _current_combinations:
                _combinations.add(existing_combination | {item, })
    for tags in _combinations:
        accumulator_dict[frozenset(tags)] = name
    return accumulator_dict


def lookup_tags(_lookup, *args):
    r"""
    >>> lookup = (
    ...     ('item_1', ('a')),
    ...     ('item_2', ('a', 'b', ('c', 'd'))),
    ...     ('item_3', ('a', 'b', ('c', 'd'), ('e', 'f'))),
    ...     ('default', ()),
    ... )
    >>> lookup_tags = functools.partial(lookup_tags, functools.reduce(_reducer_parse_single_criteria, lookup, {}))
    >>> lookup_tags('a')
    'item_1'
    >>> lookup_tags('a', 'b', 'c')
    'item_2'
    >>> lookup_tags('a', 'b', 'd', 'f')
    'item_3'
    >>> lookup_tags()
    'default'
    >>> lookup_tags('a', 'c')
    Traceback (most recent call last):
    KeyError: frozenset({'a', 'c'})

    #>>> lookup_tags('unknown')
    #'default'
    """
    return _lookup[frozenset(args)]


def items_pipeline(items, *funcs):
    """
    For each item - apply the function transforms in order
    Items are individual and atomic and could be done in parallel
    """
    for item in items:
        for func in funcs:
            item = func(item)
        yield item

# ---

def func_get_items(url):
    #data = requests.get(url, headers={'content-type': 'application/json'}).json()
    return None
def func_get_item(item):
    return item
def func_identify_tags(item):
    return item
def func_categorise_item(item):
    return item

