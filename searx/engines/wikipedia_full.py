# SPDX-License-Identifier: AGPL-3.0-or-later
"""Wikipedia full-lead extract engine.

The stock Wikipedia engine uses the REST v1 page *summary*, which is often only
a one-line description. This engine uses the MediaWiki Action API with
``prop=extracts`` and ``exintro=1`` to return the plain-text lead section.

It is intentionally placed in its own category (``wikipedia-full``) so normal
category searches do not run it. Yonder requests it explicitly from its deferred
sidebar lookup.
"""

import re
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
            "prop": "extracts|pageimages|info|extlinks",
            "inprop": "url",
            "ellimit": "50",
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


PROFILE_LINK_DOMAINS = {
    "x.com": ("X", re.compile(r"^/[A-Za-z0-9_]{1,15}/?$"), re.compile(r"/(?:i|intent|share|status|home|search|hashtag|login|signup|settings)\b", re.I)),
    "twitter.com": ("X", re.compile(r"^/[A-Za-z0-9_]{1,15}/?$"), re.compile(r"/(?:i|intent|share|status|home|search|hashtag|login|signup|settings)\b", re.I)),
    "instagram.com": ("Instagram", re.compile(r"^/[A-Za-z0-9._]{1,30}/?$"), re.compile(r"/(?:p|reel|reels|explore|accounts|stories|direct)\b", re.I)),
    "youtube.com": ("YouTube", re.compile(r"^/(?:@[A-Za-z0-9_.-]{2,}|channel/UC[A-Za-z0-9_-]{10,}|user/[A-Za-z0-9_.-]{2,}|c/[A-Za-z0-9_.-]{2,})/?$"), re.compile(r"/(?:watch|playlist|results|shorts|feed|embed)\b", re.I)),
    "tiktok.com": ("TikTok", re.compile(r"^/@[A-Za-z0-9_.-]{1,30}/?$"), re.compile(r"/(?:video|photo|music|tag|discover|foryou)\b", re.I)),
    "facebook.com": ("Facebook", re.compile(r"^/[A-Za-z0-9.]{3,}/?$"), re.compile(r"/(?:posts|photos|photo|watch|groups|events|reel|reels|stories|marketplace|login|help)\b", re.I)),
    "twitch.tv": ("Twitch", re.compile(r"^/[A-Za-z0-9_]{1,25}/?$"), re.compile(r"/(?:videos|directory|p|clip|clips|s|settings|search|downloads)\b", re.I)),
    "kick.com": ("Kick", re.compile(r"^/[A-Za-z0-9_]{1,25}/?$"), re.compile(r"/(?:video|videos|category|categories|clips|search|browse|following)\b", re.I)),
}


def profile_links(extlinks):
    seen = set()
    links = []
    for item in extlinks or []:
        raw = item.get("url") if isinstance(item, dict) else item
        if not isinstance(raw, str):
            continue
        parsed = urllib.parse.urlparse(raw)
        host = parsed.hostname.lower().removeprefix("www.") if parsed.hostname else ""
        if parsed.scheme not in ("http", "https") or not host:
            continue
        pattern = PROFILE_LINK_DOMAINS.get(host)
        if pattern is None:
            continue
        title, path_pattern, reject = pattern
        if reject.search(parsed.path) or not path_pattern.match(parsed.path):
            continue
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        if url in seen:
            continue
        seen.add(url)
        links.append({"title": title, "url": url})
        if len(links) >= 12:
            break
    return links


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

    urls = [{"title": "Wikipedia", "url": fullurl}]
    urls.extend(profile_links(page.get("extlinks")))

    return [
        {
            "infobox": title,
            "id": fullurl,
            "content": extract,
            "img_src": thumbnail,
            "urls": urls,
        }
    ]


def fetch_traits(engine_traits):
    fetch_wikimedia_traits(engine_traits)
