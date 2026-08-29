# test_version_utils.py
"""Быстрые тесты сравнения версий."""
from version_utils import compare_versions, is_update_available, normalize_version


def test_compare_versions():
    assert compare_versions("1.9.7", "1.9.7") == 0
    assert compare_versions("1.9.7", "1.9.7b") == -1
    assert compare_versions("1.9.7b", "1.9.7") == 1
    assert compare_versions("1.9.7", "1.10.0") == -1
    assert compare_versions("1.10.1", "1.10.0") == 1
    assert compare_versions("v1.10.1", "1.10.1") == 0

    # Баг с тегом 1.02 на GitHub
    assert normalize_version("1.02") == "1.0.2"
    assert compare_versions("1.0.3", "1.02") == 1
    assert compare_versions("1.02", "1.0.3") == -1
    assert is_update_available("1.0.3", "1.02") is False

    assert is_update_available("1.9.7", "1.10.1") is True
    assert is_update_available("1.10.1", "1.10.1") is False
    assert is_update_available("1.10.2", "1.10.1") is False
    print("OK: all version_utils tests passed")


if __name__ == "__main__":
    test_compare_versions()
