import os

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(path):
    url = static(path)
    full_path = os.path.join(settings.BASE_DIR, "static", path)
    try:
        version = int(os.path.getmtime(full_path))
    except OSError:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}v={version}"
