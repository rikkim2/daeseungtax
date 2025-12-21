""" filters.py
"""
from django.utils.http import urlquote


# collection


def filter_getitem(value, arg):
    return value.get(arg, '')


def filter_getat(value, arg):
    try:
        return value[int(arg)]
    except Exception as e:
        return None


def filter_notinappend(a, b):
    if b not in a:
        a.append(b)
    return a


def filter_union(a, b):
    return set(a) | set(b)


# math


def filter_divide(value, arg):
    return float(value) / float(arg)


def filter_mod(value, arg):
    return int(value) % int(arg)


def filter_min(a, b):
    return min(a, b)


def filter_max(a, b):
    return max(a, b)


# converting


def filter_int(value):
    return int(value)


# type


def filter_type(value):
    return str(type(value))


# str


def filter_endswith(value, arg):
    return value.endswith(arg)


def filter_quote(a):
    return urlquote(a)