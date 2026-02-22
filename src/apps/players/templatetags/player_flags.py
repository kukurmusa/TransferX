from django import template

register = template.Library()

_ALIASES = {
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",
    "united kingdom": "GB",
    "uk": "GB",
    "great britain": "GB",
    "united states": "US",
    "usa": "US",
    "u.s.a.": "US",
    "south korea": "KR",
    "north korea": "KP",
    "czech republic": "CZ",
    "ivory coast": "CI",
    "cote d'ivoire": "CI",
    "holland": "NL",
}


def _flag_from_code(code: str) -> str:
    if len(code) != 2 or not code.isalpha():
        return ""
    code = code.upper()
    return chr(0x1F1E6 + ord(code[0]) - ord("A")) + chr(
        0x1F1E6 + ord(code[1]) - ord("A")
    )


@register.filter(name="country_flag")
def country_flag(value: str | None) -> str:
    if not value:
        return ""
    key = value.strip().lower()
    if len(key) == 2 and key.isalpha():
        return _flag_from_code(key)
    if key in _ALIASES:
        return _flag_from_code(_ALIASES[key])
    return "🏳️"
