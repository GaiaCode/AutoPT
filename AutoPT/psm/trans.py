from typing import Literal


def router(state) -> Literal["Scan", "Vuln_select", "Inquire", "Exploit", "Check", "__end__"]:
    # --- BLOCCO DI DEBUG ---
    sender = state["sender"]
    last_message_content = state["message"][-1].content
    
    print("\n" + "="*20 + " DEBUG ROUTER " + "="*20)
    print(f"Stato di partenza (sender): {sender}")
    print(f"Ultimo messaggio ricevuto: '{last_message_content[:100]}...'") # Stampiamo solo i primi 100 caratteri
    
    # Determiniamo la prossima destinazione
    next_state = ""
    if sender == "Scan":
        next_state = "Vuln_select"
    elif sender == "Vuln_select":
        next_state = "Inquire"
    elif sender == "Inquire":
        next_state = "Exploit"
    elif sender == "Exploit":
        next_state = "Check"
    elif sender == "Check":
        if "Successfully exploited the vulnerability" in last_message_content or "Failed to exploit the vulnerability." in last_message_content:
            next_state = "__end__"
        elif "please try again." in last_message_content:
            next_state = "Exploit"
        elif "please try another vulnerability." in last_message_content:
            next_state = "Vuln_select"
    
    print(f"Decisione del router: Prossimo stato -> {next_state}")
    print("="*54 + "\n")
    
    return next_state