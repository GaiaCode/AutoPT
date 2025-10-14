import json
import random
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def safe_parse_json(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                return None
        return None

class MockLLMClient:
    """Mock LLM per test"""
    def __init__(self, backend="mock", model="gpt-4o-mini", seed=None):
        self.backend = backend
        self.model = model
        self.prev_action = None
        self.repeat_count = 0
        self.rnd = random.Random(seed)
        log.info(f"[MockLLMClient] init backend={backend} model={model} seed={seed}")

        self.possible_actions = [
            ("head_request", "Check response headers and cookie settings."),
            ("extract_links", "Extract visible links and list them."),
            ("list_forms", "List and describe forms found on the page."),
            ("check_common_paths", "Look for public admin pages by checking common paths."),
            ("noop", "No further actions necessary.")
        ]

    def _simulate_response(self):
        if self.repeat_count >= 2 and self.prev_action is not None:
            choices = [a for a in self.possible_actions if a[0] != self.prev_action]
        else:
            choices = self.possible_actions

        action_name, action_text = self.rnd.choice(choices)
        self.prev_action = action_name
        self.repeat_count = (self.repeat_count + 1) if self.prev_action == action_name else 1

        return json.dumps({
            "text": action_text,
            "suggested_action": action_name,
            "action_params": {}
        })

    def query(self, prompt: str, max_retries=3, delay=0.5) -> dict:
        for attempt in range(1, max_retries + 1):
            raw = self._simulate_response()
            parsed = safe_parse_json(raw)
            if parsed:
                return parsed
        log.error("[MockLLMClient] Failed to produce valid JSON after retries. Returning fallback.")
        return {"text": "No valid JSON produced.", "suggested_action": "noop", "action_params": {}}

def LLMClient(backend="auto", model="gpt-4o-mini", seed=None):
    return MockLLMClient(backend="mock", model=model, seed=seed)
