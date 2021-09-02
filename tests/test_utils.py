import difflib
from pathlib import Path


test_data_root = Path(__file__).parent / 'data'


def count_diff(old_lines, new_lines):
    """Count the number of additions and removals between two sets of lines"""
    plus = 0
    minus = 0
    diff_lines = difflib.ndiff(old_lines, new_lines)
    for l in diff_lines:
        if l.startswith('+'):
            plus += 1
        if l.startswith('-'):
            minus += 1
    return plus, minus


def diff_lines(old_lines, new_lines):
    """Print the diff between two sets of lines"""
    return list(difflib.unified_diff(old_lines, new_lines))


def print_diff(old_lines, new_lines):
    print(''.join(diff_lines(old_lines, new_lines)))