from pathlib import Path

from bookforge.author import slugify

def test_slugify():
    assert slugify('Eldrik Vale') == 'eldrik-vale'
    assert slugify('') == 'author'
