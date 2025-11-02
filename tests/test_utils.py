from src.utils import html_to_text

def test_html_to_text_simple():
    html = "<p>Hello <b>world</b></p>"
    t = html_to_text(html)
    assert "Hello" in t and "world" in t

def test_html_preserves_pre():
    html = "<pre>line1\nline2</pre>"
    t = html_to_text(html)
    assert "line1" in t and "line2" in t
