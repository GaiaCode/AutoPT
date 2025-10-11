import os
import json
import random
import logging
import re
from collections import defaultdict

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ==========================================================
# load_prompt helper (versione robusta e sicura)
# ==========================================================
def load_prompt(filename: str, **kwargs) -> str:
    """
    Carica e rende sicuro un template di prompt.
    - Cerca file in agent/src e poi nella working dir
    - Sostituisce placeholder mancanti con stringa vuota
    - Escapa campi posizionali come {} o {0} (li trasforma in {{}} / {{0}})
    - Restituisce il template formattato o, in caso di errore, il testo grezzo
    """
    here = os.path.dirname(__file__)
    path1 = os.path.join(here, filename)
    path2 = filename

    if os.path.exists(path1):
        path = path1
    elif os.path.exists(path2):
        path = path2
    else:
        raise FileNotFoundError(f"Prompt file not found: {filename}")

    with open(path, "r", encoding="utf-8") as f:
        template = f.read()

    # --- Escapa campi posizionali vuoti o numerici che creano errori in str.format
    try:
        # {} -> {{}}   e   {0} -> {{0}}
        template = re.sub(r'(?<!\{)\{\}(?!\})', '{{}}', template)
        template = re.sub(r'(?<!\{)\{(\d+)\}(?!\})', lambda m: '{{' + m.group(1) + '}}', template)
    except Exception as e:
        log.warning("[LLMClient] load_prompt: error while escaping positional fields: %s", e)

    # Fallback per placeholder mancanti
    safe_kwargs = defaultdict(str)
    safe_kwargs.update(kwargs)

    try:
        rendered = template.format_map(safe_kwargs)
        return rendered
    except Exception as e:
        log.error("[LLMClient] load_prompt: unexpected error during format: %s", e)
        # fallback: restituiamo comunque il template grezzo per non interrompere il flusso
        return template

# ==========================================================
# Mock LLM client
# ==========================================================
class MockLLMClient:
    """
    Mock LLM per test: restituisce una scelta di azione coerente.
    Comportamento:
      - supporta seed per riproducibilità
      - se la stessa azione viene suggerita 2 volte, al passo successivo forza variazione
      - query(prompt) -> dict with keys 'text','suggested_action','action_params'
    """
    def __init__(self, backend="mock", model="gpt-4o-mini", seed=None):
        self.backend = backend
        self.model = model
        self.prev_action = None
        self.repeat_count = 0
        self.rnd = random.Random(seed)
        log.info("[MockLLMClient] init backend=%s model=%s seed=%s", backend, model, seed)

        # Possibili azioni coerenti con react_agent
        self.possible_actions = [
            ("head_request", "Check response headers and cookie settings."),
            ("extract_links", "Extract visible links and list them."),
            ("list_forms", "List and describe forms found on the page."),
            ("check_common_paths", "Look for public admin pages by checking common paths."),
            ("crawl", "Crawl internal links (depth=1) and record discovered endpoints."),
            ("noop", "No further actions necessary.")
        ]

    def query(self, prompt: str) -> dict:
        """
        Simula risposta LLM: ritorna dict(text, suggested_action, action_params).
        Il prompt non viene realmente interpretato (mock), ma solo loggato.
        """
        log.debug("[MockLLMClient] query prompt preview: %s", prompt[:300].replace("\n", " "))

        # Se ripetuto 2 volte, forza un’azione diversa
        if self.repeat_count >= 2 and self.prev_action is not None:
            choices = [a for a in self.possible_actions if a[0] != self.prev_action]
            action_name, action_text = self.rnd.choice(choices)
            self.repeat_count = 0
        else:
            action_name, action_text = self.rnd.choice(self.possible_actions)

        # Aggiorna contatori
        if action_name == self.prev_action:
            self.repeat_count += 1
        else:
            self.repeat_count = 1
        self.prev_action = action_name

        # Esempio semplice di params
        action_params = {}
        if action_name in ("head_request", "get_page"):
            action_params = {}
        elif action_name == "post_form":
            action_params = {"path": "/login", "data": {"username": "test", "password": "test"}}
        elif action_name in ("check_common_paths", "extract_links", "list_forms", "crawl"):
            action_params = {}

        return {
            "text": action_text,
            "suggested_action": action_name,
            "action_params": action_params
        }

# ==========================================================
# Factory LLMClient
# ==========================================================
def LLMClient(backend="auto", model="gpt-4o-mini", seed=None):
    """
    Factory: se backend == "openai" -> (placeholder) implementare client reale,
    altrimenti ritorna MockLLMClient.
    """
    if backend == "auto":
        if os.getenv("OPENAI_API_KEY"):
            log.info("[LLMClient factory] OPENAI_API_KEY detected, but real backend not implemented. Falling back to mock.")
            return MockLLMClient(backend="openai", model=model, seed=seed)
        else:
            return MockLLMClient(backend="mock", model=model, seed=seed)

    if backend.lower() in ("mock",):
        return MockLLMClient(backend="mock", model=model, seed=seed)

    # Fallback generico
    return MockLLMClient(backend=backend, model=model, seed=seed)
