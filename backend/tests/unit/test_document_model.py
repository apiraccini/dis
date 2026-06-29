from src.models.document import normalize_tags


def test_normalize_tags_lowercases() -> None:
    assert normalize_tags(['Compliance', 'HR']) == ['compliance', 'hr']


def test_normalize_tags_strips_whitespace() -> None:
    assert normalize_tags(['  compliance  ', '\thr\t']) == ['compliance', 'hr']


def test_normalize_tags_dedupes_after_normalization() -> None:
    assert normalize_tags(['Compliance', ' compliance ', 'COMPLIANCE']) == ['compliance']


def test_normalize_tags_drops_empty_strings() -> None:
    assert normalize_tags(['compliance', '', '  ', 'hr']) == ['compliance', 'hr']


def test_normalize_tags_empty_list_returns_empty_list() -> None:
    assert normalize_tags([]) == []


def test_normalize_tags_preserves_order_of_first_occurrence() -> None:
    assert normalize_tags(['b', 'a', 'B', 'A']) == ['b', 'a']


def test_normalize_tags_none_returns_empty_list() -> None:
    assert normalize_tags(None) == []


def test_normalize_tags_returns_new_list() -> None:
    original = ['Compliance']
    result = normalize_tags(original)
    assert result == ['compliance']
    assert original == ['Compliance']
