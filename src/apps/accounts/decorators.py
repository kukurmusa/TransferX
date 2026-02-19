from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from .utils import is_buyer, is_seller


def seller_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_seller(request.user):
            return HttpResponseForbidden("Seller access required")
        return view_func(request, *args, **kwargs)

    return _wrapped


def buyer_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_buyer(request.user):
            return HttpResponseForbidden("Buyer access required")
        return view_func(request, *args, **kwargs)

    return _wrapped
