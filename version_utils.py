# version_utils.py
"""Сравнение версий Zapret и приложения (1.9.7, 1.9.7b, 1.10.1, 1.02)."""
import re

_VERSION_RE = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)([a-zA-Z]*)$')
_TWO_PART_RE = re.compile(r'^v?(\d+)\.(\d+)$')


def parse_version(version):
    """
    Разбирает строку версии на (major, minor, patch, suffix).

    Поддерживает:
    - 1.10.1, 1.9.7b, v1.0.3
    - 1.02 -> 1.0.2 (короткий тег GitHub)
    - 1.10 -> 1.10.0
    """
    if not version:
        return None

    cleaned = version.strip().lstrip('v')

    match = _VERSION_RE.match(cleaned)
    if match:
        return (
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            match.group(4).lower(),
        )

    match = _TWO_PART_RE.match(cleaned)
    if match:
        major = int(match.group(1))
        minor_part = match.group(2)

        # 1.02 -> 1.0.2
        if len(minor_part) == 2 and minor_part.startswith('0'):
            return (major, 0, int(minor_part[1]), '')

        return (major, int(minor_part), 0, '')

    return None


def normalize_version(version):
    """Приводит версию к читаемому виду: 1.02 -> 1.0.2."""
    parsed = parse_version(version)
    if not parsed:
        return version.strip().lstrip('v')

    major, minor, patch, suffix = parsed
    normalized = f"{major}.{minor}.{patch}"
    if suffix:
        normalized += suffix
    return normalized


def compare_versions(v1, v2):
    """
    Сравнивает две версии.
    Возвращает -1 если v1 < v2, 0 если равны, 1 если v1 > v2.
    """
    p1 = parse_version(v1)
    p2 = parse_version(v2)

    if p1 is None or p2 is None:
        n1 = normalize_version(v1) if p1 else str(v1)
        n2 = normalize_version(v2) if p2 else str(v2)
        if n1 == n2:
            return 0
        p1 = parse_version(n1)
        p2 = parse_version(n2)
        if p1 is None or p2 is None:
            return 0

    if p1[:3] != p2[:3]:
        return -1 if p1[:3] < p2[:3] else 1

    suffix1, suffix2 = p1[3], p2[3]
    if suffix1 == suffix2:
        return 0

    if not suffix1 and suffix2:
        return -1
    if suffix1 and not suffix2:
        return 1

    return -1 if suffix1 < suffix2 else 1


def is_update_available(local_version, remote_version):
    """True, если remote_version новее local_version."""
    if not local_version or not remote_version:
        return False
    return compare_versions(local_version, remote_version) < 0
