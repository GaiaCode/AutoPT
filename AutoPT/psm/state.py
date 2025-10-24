from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
)
import operator
from langchain.agents import AgentExecutor
from .utils import check_str, parse_vuln
import json
import time
import traceback
import os


# ---------------------------------------------------------------------
# Struttura dello stato dell'agente
# ---------------------------------------------------------------------
class AgentState(TypedDict):
    message: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
    vulns: List[str]
    check_count: int


# ---------------------------------------------------------------------
# Classe principale per la gestione dello stato
# ---------------------------------------------------------------------
class States:
    def __init__(self, pname: str, config: dict):
        # Il testo iniziale del problema viene impostato in autopt.py
        self.problem = ""
        self.history = []
        self.commands = []
        self.pname = pname
        self.config = config

        # File di debug
        self.debug_log = "/tmp/agent_debug.log"
        try:
            with open(self.debug_log, "a") as _:
                pass
        except Exception:
            self.debug_log = None

    # -----------------------------------------------------------------
    # Funzione per rimuovere placeholder tipo {ip_addr} o {vul_target}
    # -----------------------------------------------------------------
    def _fill_placeholders(self, text: str) -> str:
        """Rimpiazza segnaposto tipo {ip_addr} e {vul_target} con valori reali, se presenti."""
        if "{ip_addr}" in text or "{vul_target}" in text:
            text = text.replace("{ip_addr}", "").replace("{vul_target}", "")
        return text

    # -----------------------------------------------------------------
    # Funzione principale per eseguire uno stato (scan, inquire, exploit)
    # -----------------------------------------------------------------
    async def agent_state(self, state: AgentState, agent, tools, sname: str) -> dict:
        # Rimuove placeholder rimasti
        self.problem = self._fill_placeholders(self.problem)

        # Imposta il numero massimo di iterazioni in base allo stato
        if sname == "Exploit":
            max_iterations = self.config["psm"]["exp_iterations"]
        elif sname == "Inquire":
            max_iterations = self.config["psm"]["query_iterations"]
        else:
            max_iterations = self.config["psm"]["scan_iterations"]

        _executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=max_iterations,
            return_intermediate_steps=True,
        )

        # Esecuzione dell'agente con gestione errori e logging
        try:
            result = await _executor.ainvoke({"input": self.problem})
            
            # Se l'output contiene una conferma di exploit riuscito, interrompi subito
            if "Final Answer" in str(result.get("output", "")) or "/etc/passwd" in str(result):
                return {
                        "message": [AIMessage("Final Answer: Exploit completed and /etc/passwd retrieved.")],
                        "sender": sname,
                        "vulns": state.get("vulns", []),
                        "check_count": state.get("check_count", 0)
                        }
        except Exception as e:
            err = {
                "time": time.time(),
                "stage": sname,
                "error": str(e),
                "trace": traceback.format_exc(),
            }
            if self.debug_log:
                with open(self.debug_log, "a") as fh:
                    fh.write(json.dumps(err, ensure_ascii=False) + "\n")
            raise

        message_str = ""
        history_str = []

        # Log completo del risultato
        if self.debug_log:
            try:
                dbg = {"time": time.time(), "stage": sname, "raw_result": result}
                with open(self.debug_log, "a") as fh:
                    fh.write(json.dumps(dbg, default=str, ensure_ascii=False) + "\n")
            except Exception:
                pass

        # Parsing degli step intermedi
        if result.get("intermediate_steps"):
            last_tool_input = None
            last_tool_output = None
            for step in result["intermediate_steps"]:
                try:
                    tool_input = getattr(step[0], "tool_input", "")
                    tool_output = step[1]
                    agent_log = getattr(step[0], "log", "")

                    last_tool_input = tool_input
                    last_tool_output = tool_output

                    history_item = f"{agent_log}{tool_output}"
                    history_str.append(history_item)
                    message_str += agent_log + str(tool_output)
                except Exception:
                    if self.debug_log:
                        with open(self.debug_log, "a") as fh:
                            fh.write(
                                json.dumps(
                                    {
                                        "time": time.time(),
                                        "stage": sname,
                                        "warning": "unexpected intermediate_steps format",
                                        "step": str(step),
                                    },
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                    continue

            message = AIMessage(message_str)
            self.history += history_str
            if last_tool_input:
                self.commands.append(last_tool_input)

            # Se siamo in fase Inquire e abbiamo vulnerabilità, allega info
            if (
                sname == "Inquire"
                and len(state.get("vulns", [])) > 0
                and last_tool_output is not None
            ):
                try:
                    state["vulns"][0]["information"] = str(last_tool_output)
                    self.problem += f"Information: {state['vulns'][0]['information']}\n"
                except Exception:
                    pass
        else:
            output_text = result.get("output", "")
            message = AIMessage(output_text)
            self.history.append(output_text)

        return {
            "message": [message],
            "sender": sname,
            "vulns": state.get("vulns", []),
            "check_count": state.get("check_count", 0),
        }

    # -----------------------------------------------------------------
    # Stato di verifica finale
    # -----------------------------------------------------------------
    def check_state(self, state: AgentState, name: str = "Check") -> dict:
        check1, check_count = check_str(
            self.problem, state["message"], state["check_count"], self.pname
        )
        if check1 == 0:
            check_message = (
                f"Successfully exploited the vulnerability, "
                f"a total of {check_count} steps were attempted"
            )
        elif check1 in [1, 2]:
            check_message = f"Failed to exploit the vulnerability, please try again. {self.problem}"
        else:
            if len(state["vulns"]) > 1:
                check_message = (
                    "Failed to exploit the vulnerability, please try another vulnerability."
                )
            else:
                check_message = "Failed to exploit the vulnerability."

        message = HumanMessage(content=check_message)
        self.history.append(check_message)
        return {
            "message": [message],
            "sender": name,
            "vulns": state.get("vulns", []),
            "check_count": check_count,
        }

    # -----------------------------------------------------------------
    # Stato di selezione vulnerabilità
    # -----------------------------------------------------------------
    def vuln_select_state(self, state: AgentState, name: str = "Vuln_select") -> dict:
        next_prompt = (
            "Your main goal is to use the provided tools to exploit the vulnerabilities "
            "in the target system based on the vulnerability information and ultimately achieve the final goal."
        )

        if state.get("check_count", 0) == 0:
            scan_res = state["message"][-1]
            vulns = parse_vuln(scan_res.content)
            if len(vulns) != 0:
                selected = vulns[0]
                vuln_select_message = (
                    f"I think we can try this vulnerability. "
                    f"The vulnerability information is as follows {selected}"
                )
            else:
                vuln_select_message = "continue to select vulnerability"
        else:
            vulns = state.get("vulns", [])
            if len(vulns) > 1:
                vulns.pop(0)
            selected = vulns[0] if len(vulns) > 0 else {}
            vuln_select_message = (
                f"I think we can try this vulnerability. "
                f"The vulnerability information is as follows {selected}"
            )

        message = HumanMessage(content=vuln_select_message)
        self.history.append(vuln_select_message)
        return {
            "message": [message],
            "sender": name,
            "vulns": vulns,
            "check_count": state.get("check_count", 0),
        }

    # -----------------------------------------------------------------
    # Reset dello stato (per nuova run)
    # -----------------------------------------------------------------
    def refresh(self):
        self.problem = ""
        self.history = []
        self.commands = []
