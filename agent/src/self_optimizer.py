import json
import os
from collections import Counter
from datetime import datetime

LOG_DIR = "logs"
PROMPT_PATH = "planner_prompt_psm.md"

def summarize_run(log_path):
    """Legge il file JSONL e conta azioni e risultati."""
    actions = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if "action" in entry:
                    actions.append(entry["action"])
            except json.JSONDecodeError:
                continue

    stats = Counter(actions)
    return stats

def suggest_improvements(stats):
    """Suggerisce miglioramenti basati sui pattern di azioni."""
    suggestions = []

    if not stats:
        return ["Nessuna azione registrata — forse l'agente non ha eseguito nulla."]

    if stats["crawl"] > 3:
        suggestions.append("Riduci la frequenza di `crawl`, eseguilo solo una volta per dominio.")

    if stats["list_forms"] == 0:
        suggestions.append("Aggiungi un passo di enumerazione form per la fase di reconnaissance.")

    if stats["extract_links"] < 2:
        suggestions.append("Esegui `extract_links` più spesso dopo un `crawl` per ampliare la coverage.")

    suggestions.append("Considera l'aggiunta di una fase di validazione automatica dei risultati.")
    return suggestions


def update_planner_prompt(suggestions):
    """Sovrascrive il planner_prompt_psm.md con un testo aggiornato."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_prompt = f"""# AutoPT Planner Prompt (aggiornato {timestamp})

## Obiettivo
Analizzare applicazioni web vulnerabili simulando un penetration tester autonomo.

## Linee guida aggiornate
- Usa un approccio ciclico: osserva → pianifica → agisci → valuta.
- Prediligi azioni ad alto valore informativo (link discovery, form extraction, head request).
- Evita ripetizioni eccessive di azioni già esplorate.

## Suggerimenti di ottimizzazione
"""

    for s in suggestions:
        new_prompt += f"- {s}\n"

    with open(PROMPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_prompt)

    print(f"[✓] Nuovo planner salvato in {PROMPT_PATH}")


def auto_optimize(log_path):
    print(f"[*] Running AutoPT self-optimization on {log_path}")

    stats = summarize_run(log_path)
    print("[+] Step summary:")
    for action, count in stats.items():
        print(f"    - {action}: {count}")

    suggestions = suggest_improvements(stats)
    update_planner_prompt(suggestions)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, help="Percorso del file di log JSONL")
    args = parser.parse_args()
    auto_optimize(args.log)
