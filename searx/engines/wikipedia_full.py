# SPDX-License-Identifier: AGPL-3.0-or-later
"""Wikipedia full-lead extract engine.

The stock Wikipedia engine uses the REST v1 page *summary*, which is often only
a one-line description. This engine uses the MediaWiki Action API with
``prop=extracts`` and ``exintro=1`` to return the plain-text lead section.

It is intentionally placed in its own category (``wikipedia-full``) so normal
category searches do not run it. Yonder requests it explicitly from its deferred
sidebar lookup.
"""

import urllib.parse

from searx import network as _network
from searx import utils
from searx.engines import wikipedia as wikipedia_engine
from searx.engines.wikipedia import fetch_wikimedia_traits

# about
about = {
    "website": "https://www.wikipedia.org/",
    "wikidata_id": "Q52",
    "official_api_documentation": "https://www.mediawiki.org/wiki/API:Main_page",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

language_support = True
display_type = ["infobox"]


def get_wiki_params(sxng_locale, eng_traits):
    """Return the Wikipedia language tag and netloc for a SearXNG locale."""
    if eng_traits is None:
        return "en", "en.wikipedia.org"
    eng_tag = eng_traits.get_region(sxng_locale, eng_traits.get_language(sxng_locale, "en"))
    try:
        wiki_netloc = eng_traits.custom["wiki_netloc"].get(eng_tag, "en.wikipedia.org")
    except (AttributeError, KeyError):
        # The dedicated engine may not have its own generated trait cache yet.
        # The stock wikipedia engine's traits are sufficient for the netloc map.
        wiki_netloc = "en.wikipedia.org"
    return eng_tag, wiki_netloc


def request(query, params):
    """Request the plain-text lead section from the MediaWiki Action API."""
    if query.islower():
        query = query.title()

    eng_traits = getattr(wikipedia_engine, "traits", None)
    if eng_traits is None:
        eng_traits = globals().get("traits")
    _eng_tag, wiki_netloc = get_wiki_params(params["searxng_locale"], eng_traits)
    params["url"] = f"https://{wiki_netloc}/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "extracts|pageimages|info",
            "inprop": "url",
            "exintro": "1",
            "explaintext": "1",
            "redirects": "1",
            "titles": query,
            "pithumbsize": "500",
        }
    )
    params["raise_for_httperror"] = False
    params["soft_max_redirects"] = 2
    return params


def response(resp):
    if resp.status_code in (400, 404):
        return []

    _network.raise_for_httperror(resp)

    try:
        api_result = resp.json()
    except Exception:  # pylint: disable=broad-except
        return []

    pages = api_result.get("query", {}).get("pages", [])
    if not pages:
        return []

    page = pages[0]
    if page.get("missing") or page.get("invalid"):
        return []

    extract = page.get("extract") or ""
    fullurl = page.get("fullurl") or ""
    if not extract or not fullurl:
        return []

    title = utils.html_to_text(page.get("title") or "")
    thumbnail = (page.get("thumbnail") or {}).get("source")

    return [
        {
            "infobox": title,
            "id": fullurl,
            "content": extract,
            "img_src": thumbnail,
            "urls": [{"title": "Wikipedia", "url": fullurl}],
        }
    ]


def fetch_traits(engine_traits):
    fetch_wikimedia_traits(engine_traits)
