import re

from django.template.defaultfilters import linebreaksbr
from django.utils.html import escape
from django.utils.safestring import mark_safe


DEFAULT_DESC_HTML = "<p>Chua cap nhat mo ta chi tiet cho can ho nay.</p>"


def render_description_html(raw_description):
    content = (raw_description or "").strip()
    if not content:
        return mark_safe(DEFAULT_DESC_HTML)

    if re.search(r"<[a-z][\s\S]*>", content, re.IGNORECASE):
        return mark_safe(content)

    return mark_safe(linebreaksbr(escape(content)))
