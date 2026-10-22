# SPDX-License-Identifier: AGPL-3.0-or-later

from searx.engines import wikipedia_full


class FakeTraits:
    custom = {"wiki_netloc": {"en": "en.wikipedia.org"}}

    def get_region(self, _locale, _default):
        return "en"

    def get_language(self, _locale, _default):
        return "en"


class FakeResponse:
    status_code = 200

    def json(self):
        return {
            "query": {
                "pages": [
                    {
                        "title": "xQc",
                        "extract": "Félix Lengyel is a Canadian online streamer. This is the full lead.",
                        "fullurl": "https://en.wikipedia.org/wiki/XQc",
                        "thumbnail": {"source": "https://thumb.wikimedia.org/xqc.jpg"},
                    }
                ]
            }
        }


def test_request_uses_mediawiki_extract_api():
    wikipedia_full.wikipedia_engine.traits = FakeTraits()
    params = {"searxng_locale": "en"}
    wikipedia_full.request("xQc", params)
    assert params["url"].startswith("https://en.wikipedia.org/w/api.php?")
    assert "prop=extracts%7Cpageimages%7Cinfo" in params["url"]
    assert "exintro=1" in params["url"]
    assert "explaintext=1" in params["url"]


def test_response_returns_infobox_with_full_lead_and_image():
    results = wikipedia_full.response(FakeResponse())
    assert len(results) == 1
    assert results[0]["infobox"] == "xQc"
    assert results[0]["content"].endswith("This is the full lead.")
    assert results[0]["img_src"] == "https://thumb.wikimedia.org/xqc.jpg"
    assert results[0]["urls"] == [{"title": "Wikipedia", "url": "https://en.wikipedia.org/wiki/XQc"}]
