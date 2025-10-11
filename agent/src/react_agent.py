# agent/src/react_agent.py
import os
import json
import random
from llm_client import LLMClient, load_prompt
from environmentreact import Environment

# === ReAct Agent integrato con LLM (AutoPT-like) ===

def init_llm():
    """
    Inizializza il client LLM in base all'ambiente.
    - Se OPENAI_API_KEY è presente, usa OpenAI (non implementato qui)
    - Altrimenti usa backend mock
    """
    backend = os.getenv("LLM_BACKEND", "auto")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    seed_env = os.getenv("LLM_SEED", None)
    seed = int(seed_env) if seed_env is not None else None

    llm = LLMClient(backend=backend, model=model, seed=seed)
    print(f"[+] LLM initialized → backend={backend}, model={model}, seed={seed}")
    return llm


def run_react(base_url: str, allow_posts=True, seed=None, max_steps=10):
    """
    Esegue un ciclo base ReAct / AutoPT-like.
    1. Osserva lo stato
    2. Pianifica un’azione con l’LLM
    3. Esegue l’azione con l’environment
    4. Mostra i risultati step-by-step
    """
    print(f"\n[*] Starting ReAct run on {base_url}\n")

    if seed is not None:
        random.seed(seed)
    env = Environment(base_url, allow_posts)
    llm = init_llm()

    observation = env.reset()
    history = []

    for step in range(1, max_steps + 1):
        print(f"\n=== STEP {step} ===")

        # Carica il prompt di pianificazione dinamica
        # IMPORTANT: aggiungiamo path="/" per coprire il placeholder {path}
        prompt = load_prompt(
            "planner_prompt_psm.md",
            observation=observation,
            url=env.current_url,
            path="/",
            goal="Eseguire una sessione di test automatizzata sul target"
        )

        # Query al modello
        response = llm.query(prompt)
        msg = response.get("text", "")
        action = response.get("suggested_action", "noop")
        params = response.get("action_params", {})

        print(f"Azione suggerita dall'LLM: {action}")
        print(f"Messaggio LLM: {msg}")

        # Esecuzione nel browser simulato / HTTP client
        result = env.step(action, params)

        # Log sintetico per leggibilità
        preview = result if isinstance(result, str) else str(result)[:500]
        print(f"Result type: {action}")
        print(f"Preview: {preview[:500]}")
        print("=================\n")

        history.append({
            "step": step,
            "action": action,
            "params": params,
            "result": result,
            "observation": observation
        })

        observation = str(result)
        if action in ["noop", "done"]:
            break

    print("\n[*] ReAct run completato.")
    return history


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", type=str, required=True)
    parser.add_argument("--allow-posts", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    run_react(base_url=args.base_url, allow_posts=args.allow_posts, seed=args.seed)
