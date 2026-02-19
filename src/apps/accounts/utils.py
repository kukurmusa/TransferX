from django.contrib.auth.models import Group


def has_group(user, name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=name).exists()


def is_admin(user) -> bool:
    return has_group(user, "admin") or user.is_superuser


def is_seller(user) -> bool:
    return has_group(user, "seller") or is_admin(user)


def is_buyer(user) -> bool:
    return has_group(user, "buyer") or is_admin(user)


def ensure_group(name: str) -> Group:
    group, _ = Group.objects.get_or_create(name=name)
    return group
