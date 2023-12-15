from django import template

register = template.Library()

@register.inclusion_tag('recurse_tree.html')
def recurse_tree(children):
    print(children)
    return {'children': children}
