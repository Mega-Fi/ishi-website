import dataclasses

import pytest

from src.models import Article


class TestArticle:
    def test_stores_title_and_url(self) -> None:
        article = Article(title="Hello", url="https://example.com/")
        assert article.title == "Hello"
        assert article.url == "https://example.com/"

    def test_is_frozen(self) -> None:
        article = Article(title="Hello", url="https://example.com/")
        with pytest.raises(dataclasses.FrozenInstanceError):
            article.title = "Mutated"  # type: ignore[misc]

    def test_equality_is_structural(self) -> None:
        a = Article(title="Same", url="https://example.com/")
        b = Article(title="Same", url="https://example.com/")
        assert a == b

    def test_inequality_when_any_field_differs(self) -> None:
        base = Article(title="A", url="https://example.com/")
        assert base != Article(title="B", url="https://example.com/")
        assert base != Article(title="A", url="https://other.com/")

    def test_is_hashable_and_usable_in_set(self) -> None:
        a = Article(title="Same", url="https://example.com/")
        b = Article(title="Same", url="https://example.com/")
        assert {a, b} == {a}
