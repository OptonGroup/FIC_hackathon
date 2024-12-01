from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='get_item')
def get_item(lst, index):
    try:
        if isinstance(lst, str):
            lst = eval(lst)
        return lst[int(index)]
    except:
        return 0 