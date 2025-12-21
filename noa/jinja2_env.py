from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2_env import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
    })
    return env