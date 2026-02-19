import os


def get_env(name, default=None, *, required=False):
    value = os.getenv(name, default)
    if required and value is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def get_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_list(name, default=None, *, separator=","):
    value = os.getenv(name)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(separator) if item.strip()]


def get_int(name, default=0):
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)
