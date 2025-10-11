# agent/src/environmentreact.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import requests
import time
import logging
from urllib.parse import urljoin, urlparse

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Environment:
    """
    Environment che espone azioni utili per AutoPT-like agent:
      - reset()
      - step(action, params)
    Azioni supportate:
      - get_page (or goto), head_request, extract_links, list_forms, post_form,
        check_common_paths, crawl, noop, done, click, input
    """

    COMMON_PATHS = [
        "/admin", "/admin/login", "/management", "/dashboard", "/login", "/admin.html",
        "/wp-admin", "/server-status", "/.git", "/config", "/.env"
    ]

    def __init__(self, base_url, allow_posts=True, headless=True, timeout=10):
        self.base_url = base_url.rstrip("/")
        self.allow_posts = allow_posts
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser = None
        self.page = None
        self.current_url = base_url
        self._last_html = ""
        self._links_cache = []

    # -----------------------
    # Browser lifecycle
    # -----------------------
    def reset(self):
        """Start Playwright browser and open base_url (rendered). Returns initial observation (string)."""
        log.info("[ENV] Resetting environment → %s", self.base_url)
        try:
            self.playwright = sync_playwright().start()
            # launch chromium (Playwright image should have browsers under /ms-playwright)
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
            self.page.goto(self.base_url, wait_until="load", timeout=self.timeout*1000)
            time.sleep(0.5)
            html = self.page.content()
            self.current_url = self.page.url
            self._last_html = html
            return self._extract_observation(html)
        except PlaywrightTimeoutError as e:
            return f"[ENV ERROR] Playwright timeout: {e}"
        except Exception as e:
            return f"[ENV ERROR] reset failed: {e}"

    def close(self):
        """Close Playwright safely."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
        log.info("[ENV] Environment closed.")

    # -----------------------
    # Helpers
    # -----------------------
    def _extract_observation(self, html):
        """Return a compact textual observation from HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string.strip() if soup.title else "Untitled"
            text = soup.get_text(separator=" ", strip=True)
            snippet = (text[:600] + "...") if len(text) > 600 else text
            return {"url": self.current_url, "title": title, "snippet": snippet}
        except Exception as e:
            return {"url": self.current_url, "error": f"obs-extract:{e}"}

    def _make_full_url(self, path_or_url):
        """Turn path or relative href into full absolute URL using base_url."""
        if not path_or_url:
            return self.base_url
        # if already absolute
        parsed = urlparse(path_or_url)
        if parsed.scheme:
            return path_or_url
        # join with base
        return urljoin(self.base_url + "/", path_or_url.lstrip("/"))

    # -----------------------
    # Action implementations
    # -----------------------
    def head_request(self, url=None):
        """Return headers and status code using requests.head (fast)."""
        target = self._make_full_url(url or self.base_url)
        try:
            r = requests.head(target, timeout=self.timeout, allow_redirects=True)
            return {"status": r.status_code, "headers": dict(r.headers)}
        except Exception as e:
            return {"error": str(e)}

    def get_page(self, url=None, wait="networkidle"):
        """Return rendered HTML for the given URL using Playwright."""
        target = self._make_full_url(url or self.base_url)
        try:
            if not self.page:
                return {"error": "browser not started"}
            self.page.goto(target, wait_until="networkidle", timeout=self.timeout*1000)
            time.sleep(0.3)
            html = self.page.content()
            self.current_url = self.page.url
            self._last_html = html
            return {"url": self.current_url, "html": html}
        except PlaywrightTimeoutError as e:
            return {"error": f"playwright_timeout: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def extract_links(self, url=None):
        """
        Extract anchors (href) and also links found in SPA router anchors.
        Returns normalized list of unique hrefs (absolute or fragment).
        """
        target = self._make_full_url(url or self.current_url)
        # try rendered HTML first (playwright)
        rendered = self.get_page(target)
        if "html" not in rendered:
            # fallback: try requests
            try:
                r = requests.get(target, timeout=self.timeout)
                html = r.text
            except Exception as e:
                return {"error": str(e), "links": []}
        else:
            html = rendered["html"]

        soup = BeautifulSoup(html, "html.parser")
        links = set()
        # normal anchors
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href:
                full = self._make_full_url(href)
                links.add(full)
        # also check JS-rendered data: scan for window.location, hrefs in scripts (best-effort)
        # return list
        links_list = sorted(links)
        # cache small set to allow crawl
        self._links_cache = links_list
        return {"url": target, "links": links_list}

    def list_forms(self, url=None):
        """Return list of forms with method/action/inputs."""
        target = self._make_full_url(url or self.current_url)
        # get rendered html
        rendered = self.get_page(target)
        if "html" not in rendered:
            return {"url": target, "forms": [], "error": rendered.get("error")}
        html = rendered["html"]
        soup = BeautifulSoup(html, "html.parser")
        forms = []
        for f in soup.find_all("form"):
            action = f.get("action") or ""
            method = (f.get("method") or "get").lower()
            inputs = []
            for inp in f.find_all(["input", "textarea", "select"]):
                inputs.append({
                    "name": inp.get("name"),
                    "type": inp.get("type") if inp.name == "input" else inp.name,
                    "value": inp.get("value")
                })
            forms.append({"action": action, "method": method, "inputs": inputs})
        return {"url": target, "forms": forms}

    def post_form(self, url=None, action="", data=None):
        """
        Perform harmless POST (if allowed) to action (path or full URL).
        Returns status and snippet.
        """
        if not self.allow_posts:
            return {"error": "POSTs not allowed by env configuration"}

        target_page = self._make_full_url(url or self.current_url)
        # resolve action relative to page
        if action and action.startswith("/"):
            full = urljoin(self.base_url + "/", action.lstrip("/"))
        elif action:
            full = self._make_full_url(action)
        else:
            full = target_page

        data = data or {}
        try:
            r = requests.post(full, data=data, timeout=self.timeout, allow_redirects=True)
            return {"url": full, "status": r.status_code, "text_preview": r.text[:800]}
        except Exception as e:
            return {"error": str(e)}

    def check_common_paths(self):
        """Check a set of common admin paths and return quick analysis (status_like)."""
        results = []
        for p in self.COMMON_PATHS:
            full = self._make_full_url(p)
            try:
                r = requests.get(full, timeout=self.timeout, allow_redirects=True)
                status_like = "likely" if r.status_code == 200 else ("possible" if r.status_code in (301,302,403) else "error")
                snippet = r.text[:400]
                # heuristic: look for "login" keyword or form
                evidence = {"keywords": [], "snippet": snippet}
                if "login" in snippet.lower():
                    evidence["keywords"].append("login")
                results.append({"path": p, "status": r.status_code, "status_like": status_like, "evidence": evidence})
            except Exception as e:
                results.append({"path": p, "status": None, "status_like": "error", "evidence": None, "error": str(e)})
        return {"base": self.base_url, "results": results}

    def crawl(self, depth=1, follow_same_host=True):
        """
        Simple crawl using Playwright rendered links (BFS up to depth).
        Returns discovered urls.
        """
        discovered = set()
        queue = [(self.current_url, 0)]
        while queue:
            url, d = queue.pop(0)
            if url in discovered or d > depth:
                continue
            discovered.add(url)
            # extract links for this url
            res = self.extract_links(url)
            links = res.get("links", [])
            for l in links:
                # optionally restrict to same host
                if follow_same_host:
                    if urlparse(l).netloc != urlparse(self.base_url).netloc:
                        continue
                queue.append((l, d+1))
        return {"base": self.base_url, "discovered": sorted(discovered)}

    # -----------------------
    # Generic step() API
    # -----------------------
    def step(self, action, params=None):
        """Dispatcher for actions. Returns structured result (dict or str)."""
        params = params or {}
        action = (action or "").lower()

        try:
            if action in ("get_page", "goto"):
                return self.get_page(params.get("url"))
            if action in ("head_request", "head"):
                return self.head_request(params.get("url"))
            if action in ("extract_links", "extract", "links"):
                return self.extract_links(params.get("url"))
            if action in ("list_forms", "forms"):
                return self.list_forms(params.get("url"))
            if action == "post_form":
                return self.post_form(params.get("url"), params.get("path", ""), params.get("data"))
            if action == "check_common_paths":
                return self.check_common_paths()
            if action == "crawl":
                depth = int(params.get("depth", 1))
                return self.crawl(depth=depth)
            if action == "noop":
                return {"result": "noop"}
            if action == "done":
                self.close()
                return {"result": "done"}
            # browser actions (optionally useful)
            if action == "click":
                selector = params.get("selector")
                if not selector:
                    return {"error": "missing selector"}
                self.page.click(selector)
                time.sleep(0.3)
                return self._extract_observation(self.page.content())
            if action == "input":
                selector = params.get("selector")
                text = params.get("text", "")
                if not selector:
                    return {"error": "missing selector"}
                self.page.fill(selector, text)
                time.sleep(0.2)
                return {"result": "input done"}
            return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

