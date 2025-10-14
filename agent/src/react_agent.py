import argparse
import logging
from llm_client import LLMClient, safe_parse_json
from environmentreact import EnvironmentReact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_react(base_url: str, seed: int = None, max_steps: int = 10):
    logger.info(f"[*] Starting ReAct run on {base_url}")

    # Inizializza LLM
    llm = LLMClient(backend="mock", model="gpt-4o-mini", seed=seed)

    # Usa EnvironmentReact come context manager
    with EnvironmentReact(base_url) as env:
        logger.info(f"[*] Browser ready at {base_url}")

        for step in range(1, max_steps + 1):
            logger.info(f"=== STEP {step} ===")
            # Simulazione prompt LLM
            prompt = f"Step {step}: observation from page."
            raw_response = llm.ask(prompt)
            action = safe_parse_json(raw_response) or {"action": "noop", "params": {}}

            action_name = action.get("action", "noop")
            action_params = action.get("params", {})

            logger.info(f"Azione suggerita: {action_name}")
            result = env.execute(action_name, action_params)  # execute deve essere implementato in EnvironmentReact
            logger.info(f"Risultato: {result}")
            logger.info("=" * 25)

    logger.info("[*] ReAct run completato.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", type=str, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    run_react(args.base_url, seed=args.seed)
