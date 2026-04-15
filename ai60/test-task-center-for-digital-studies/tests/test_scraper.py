from src.scraper import HN_URL, normalize_url


class TestNormalizeUrl:
    def test_relative_item_path_becomes_absolute(self) -> None:
        assert (
            normalize_url("item?id=12345")
            == "https://news.ycombinator.com/item?id=12345"
        )

    def test_absolute_external_url_is_preserved(self) -> None:
        external = "https://example.com/article"
        assert normalize_url(external) == external

    def test_root_relative_path_joins_against_origin(self) -> None:
        assert normalize_url("/from") == "https://news.ycombinator.com/from"

    def test_strips_surrounding_whitespace(self) -> None:
        assert (
            normalize_url("  item?id=1  ")
            == "https://news.ycombinator.com/item?id=1"
        )

    def test_accepts_custom_base(self) -> None:
        assert (
            normalize_url("page", base="https://other.example/")
            == "https://other.example/page"
        )

    def test_http_and_https_both_preserved(self) -> None:
        assert normalize_url("http://example.com/x") == "http://example.com/x"
        assert normalize_url("https://example.com/x") == "https://example.com/x"

    def test_default_base_is_hacker_news(self) -> None:
        assert HN_URL == "https://news.ycombinator.com/"
