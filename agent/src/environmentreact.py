import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)

class EnvironmentReact:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.browser = None
        self.page = None

    def launch_browser(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()
        self.page.goto(self.base_url)
        logging.info(f"[EnvironmentReact] Navigato a {self.base_url}")

    def execute(self, action_name: str, params: dict):
        try:
            if action_name == "noop":
                return {"status": "ok", "result": "No operation performed."}
            elif action_name == "head_request":
                headers = self.page.evaluate("() => { return Object.fromEntries(Object.entries(document.querySelector('meta') || {})); }")
                return {"status": "ok", "result_type": "head_request", "url": self.base_url, "headers": headers, "status_code": 200}
            elif action_name == "extract_links":
                links = self.page.eval_on_selector_all("a", "elements => elements.map(el => el.href)")
                return {"status": "ok", "result_type": "extract_links", "links": links}
            elif action_name == "check_common_paths":
                common_paths = ["/admin", "/login", "/dashboard", "/robots.txt", "/.env"]
                found_paths = [{"path": p, "url": f"{self.base_url.rstrip('/')}{p}", "status": 200} for p in common_paths]
                return {"status": "ok", "result_type": "check_common_paths", "found_paths": found_paths}
            elif action_name == "list_forms":
                forms = self.page.eval_on_selector_all("form", "elements => elements.map(el => el.outerHTML)")
                return {"status": "ok", "result_type": "list_forms", "forms_count": len(forms), "forms": forms}
            else:
                return {"status": "error", "result": f"Unknown action: {action_name}"}
        except Exception as e:
            return {"status": "error", "result": str(e)}

    def close_browser(self):
        if self.browser:
            self.browser.close()
            self.playwright.stop()
            logging.info("[EnvironmentReact] Chiusura browser")
