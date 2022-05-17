from django import template
from ..models import Jobs

import re

register = template.Library()

@register.filter
def template_cut_re(value, search):
    return re.sub(search, '', value)