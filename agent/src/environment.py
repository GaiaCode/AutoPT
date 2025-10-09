import requests

class Environment:
    def get_page(self, url: str) -> str:
        try:
            r = requests.get(url, timeout=10)
            return r.text
        except Exception as e:
            return f"Error: {e}"
