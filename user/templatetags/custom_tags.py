from django import template

register = template.Library()

@register.inclusion_tag('recurse_tree.html', takes_context=True)
def render_tree(context, children):
    print(children)
    return {'children': children}
