from bookforge.prompt.renderer import render_template
from bookforge.prompt.serialization import dumps_json


def test_render_template_deterministic_order():
    template = "A={{a}} B={{b}}"
    rendered = render_template(template, {"b": "2", "a": "1"})
    assert rendered == "A=1 B=2"


def test_render_template_serializes_objects():
    template = "DATA={{payload}}"
    rendered = render_template(template, {"payload": {"b": 2, "a": 1}})
    assert rendered.endswith(dumps_json({"a": 1, "b": 2}))
