from django import template
import re

from app.models import BlogPost
from app.models import BlogCategory

register = template.Library()

@register.filter(name='first_paragraph')
def first_paragraph(value):
    paragraphs = re.split(r'</p>|<br>|<br/>|<br />', value, flags=re.IGNORECASE)
    if paragraphs:
        return paragraphs[0]
    return ''

@register.filter
def order_by_category(blog_category):
    return blog_category.order_by('name')


@register.filter
def order_by_title(blog_posts):
    return blog_posts.order_by('title')