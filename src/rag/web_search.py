"""Official Government Web Search Engine with Whitelist Prioritization.
Prioritizes trusted portals: pmkisan.gov.in, pmfby.gov.in, myscheme.gov.in,
agriwelfare.gov.in, mnre.gov.in, and official Uttar Pradesh agriculture portals.
Supports Tavily, Serper, and out-of-the-box DuckDuckGo search fallback.
"""

import os
import re
import logging
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Trusted official government and agricultural domains
OFFICIAL_DOMAINS = [
    "pmkisan.gov.in",
    "pmfby.gov.in",
    "myscheme.gov.in",
    "agriwelfare.gov.in",
    "mnre.gov.in",
    "upagriculture.com",
    "kisan.up.gov.in",
    "up.gov.in",
    "soilhealth.dac.gov.in",
    "agricoop.nic.in",
    "icar.org.in",
    "iiwbr.icar.gov.in",
    "nabard.org",
    "farmer.gov.in",
    "dbtbharat.gov.in",
    "upagripardarshi.gov.in"
]


class OfficialWebSearcher:
    """Searches the live web for verified government scheme information,
    prioritizing official .gov.in and approved agricultural domains.
    """

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        serper_api_key: Optional[str] = None
    ):
        self.tavily_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self.serper_key = serper_api_key or os.getenv("SERPER_API_KEY")
        self.access_date = datetime.now().strftime("%Y-%m-%d")

    def search_official_web(self, query: str, max_results: int = 4) -> Dict[str, Any]:
        """Executes search with prioritized official government filtering.
        Tries Tavily -> Serper -> DuckDuckGo in sequence.
        """
        results: List[Dict[str, Any]] = []
        provider_used = "none"

        # 1. Try Tavily Search API if key is configured
        if self.tavily_key and self.tavily_key.strip():
            try:
                results = self._search_tavily(query, max_results=max_results)
                provider_used = "tavily"
            except Exception as e:
                logger.warning(f"Tavily search failed: {e}. Falling back to standard search.")

        # 2. Try Serper API if key is configured and no results yet
        if not results and self.serper_key and self.serper_key.strip():
            try:
                results = self._search_serper(query, max_results=max_results)
                provider_used = "serper"
            except Exception as e:
                logger.warning(f"Serper search failed: {e}. Falling back to standard search.")

        # 3. Universal zero-config fallback: DuckDuckGo Search
        if not results:
            try:
                results = self._search_duckduckgo(query, max_results=max_results)
                provider_used = "duckduckgo"
            except Exception as e:
                logger.warning(f"DuckDuckGo search failed: {e}")

        # Post-process, verify official standing, and rank
        processed_results = self._rank_and_verify(results, query)

        has_official = any(r.get("is_official") for r in processed_results)
        has_results = len(processed_results) > 0

        return {
            "found": has_results,
            "has_official_source": has_official,
            "provider": provider_used,
            "query": query,
            "results": processed_results,
            "access_date": self.access_date
        }

    def _search_tavily(self, query: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """Queries Tavily API with domain prioritization."""
        from tavily import TavilyClient

        client = TavilyClient(api_key=self.tavily_key)
        # Targeted agricultural query
        refined_query = f"{query} Indian government scheme official"
        response = client.search(
            query=refined_query,
            search_depth="advanced",
            max_results=max_results + 2,
            include_domains=OFFICIAL_DOMAINS
        )
        items = response.get("results", [])
        if not items:
            # Broaden if strict domain filter returned 0
            response = client.search(query=refined_query, max_results=max_results)
            items = response.get("results", [])

        out = []
        for it in items:
            out.append({
                "title": it.get("title", ""),
                "url": it.get("url", ""),
                "snippet": it.get("content", ""),
                "score": it.get("score", 0.0)
            })
        return out

    def _search_serper(self, query: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """Queries Serper Google Search API."""
        import json
        import urllib.request

        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": f"{query} site:gov.in OR site:nic.in", "num": max_results})
        headers = {"X-API-KEY": self.serper_key, "Content-Type": "application/json"}
        req = urllib.request.Request(url, data=payload.encode("utf-8"), headers=headers)

        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            out = []
            for item in data.get("organic", [])[:max_results]:
                out.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            return out

    def _search_duckduckgo(self, query: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """Queries DuckDuckGo via DDGS prioritizing government domains."""
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        out = []
        # Query 1: Targeted gov.in search
        gov_query = f"{query} site:gov.in"
        with DDGS() as ddgs:
            try:
                for r in ddgs.text(gov_query, max_results=max_results):
                    out.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
            except Exception:
                pass

            # If targeted gov query returned fewer than 2 results, run general query
            if len(out) < 2:
                try:
                    for r in ddgs.text(f"{query} scheme India official", max_results=max_results):
                        # Avoid duplicates
                        if not any(existing["url"] == r.get("href") for existing in out):
                            out.append({
                                "title": r.get("title", ""),
                                "url": r.get("href", ""),
                                "snippet": r.get("body", "")
                            })
                except Exception:
                    pass

        return out[:max_results]

    def _rank_and_verify(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Verifies relevance, classifies official vs third-party sources, and sorts official first."""
        ranked = []
        for r in results:
            url = r.get("url", "")
            title = r.get("title", "")
            snippet = r.get("snippet", "")

            if not url or not title:
                continue

            parsed = urlparse(url)
            hostname = parsed.netloc.lower()

            is_gov_domain = self.is_official_domain(hostname)
            is_relevant = self.is_relevant_result(title, snippet, url, query)

            # An official source must be BOTH on a verified government domain AND relevant to the user's query
            is_official = is_gov_domain and is_relevant

            # Filter out blacklisted/clickbait non-official domains
            if not is_gov_domain and any(bad in hostname for bad in ["facebook.com", "twitter.com", "instagram.com", "pinterest.com", "quora.com", "reddit.com"]):
                continue

            ranked.append({
                "title": title.strip(),
                "url": url.strip(),
                "snippet": snippet.strip()[:350],
                "is_official": is_official,
                "is_relevant": is_relevant,
                "domain": hostname,
                "source_type": "official_web" if is_official else "web_reference",
                "access_date": self.access_date
            })

        # Sort so official sources appear first
        ranked.sort(key=lambda x: (1 if x["is_official"] else 0), reverse=True)
        return ranked

    @staticmethod
    def is_relevant_result(title: str, snippet: str, url: str, query: str) -> bool:
        """Requirement 5: Verifies that the search result is genuinely relevant to the farmer's query."""
        query_lower = query.lower()
        text_lower = f"{title} {snippet} {url}".lower()

        tokens = [w for w in re.findall(r"[\w\u0900-\u097F]+", query_lower) if len(w) > 2]
        generic_stopwords = {
            "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
            "the", "and", "for", "with", "from", "this", "that", "have", "has", "had",
            "can", "could", "will", "would", "shall", "should", "about", "tell", "give",
            "scheme", "schemes", "yojana", "योजना", "government", "sarkar", "सरकार",
            "farmer", "farmers", "kisan", "किसान", "india", "bharat", "भारत",
            "apply", "application", "deadline", "date", "online", "portal", "subsidy", "अनुदान",
            "official", "kya", "kab", "kaise", "kahan", "kise", "aur", "hai", "hain", "hoga",
            "hogi", "wala", "wali", "wale", "karo", "kare", "karen", "me", "mein", "par", "se",
            "ko", "ki", "ke", "ka", "site", "gov", "अंतिम", "तिथि"
        }
        substantive = [t for t in tokens if t not in generic_stopwords]
        if not substantive:
            return any(t in text_lower for t in tokens)

        matches = sum(1 for st in substantive if st in text_lower)
        if len(substantive) >= 3:
            return matches >= 2
        return matches >= 1

    @staticmethod
    def is_official_domain(hostname: str) -> bool:
        """Determines if a domain is a verified government or official agricultural portal."""
        hostname = hostname.lower()
        if hostname.endswith(".gov.in") or hostname.endswith(".nic.in") or hostname.endswith(".up.gov.in"):
            return True
        for off in OFFICIAL_DOMAINS:
            if off in hostname:
                return True
        return False
