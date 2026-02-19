from django import template

from apps.accounts.utils import is_buyer, is_seller

register = template.Library()


@register.filter
def user_is_seller(user):
    return is_seller(user)


@register.filter
def user_is_buyer(user):
    return is_buyer(user)
