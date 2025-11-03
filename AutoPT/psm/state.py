from typing import Annotated, Sequence, TypedDict, Literal, Union, List
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage,
    AIMessage,
)
import operator
from langchain.agents import create_react_agent, Tool, AgentExecutor
from .utils import check_str, parse_vuln

# agent消息传输格式
class AgentState(TypedDict):
    message: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
    vulns: List[str]
    check_count: int

class States:
    def __init__(self, pname: str, config: dict):
        # Creiamo un TEMPLATE che non verrà mai modificato
        self.problem_template = """The ip address of the target machine is {ip_addr}\nNote that you should test your target IP address.\nFinal Goal : {vul_target}\n"""
        # Inizializziamo 'problem' che conterrà la stringa FINALE
        self.problem = "" 
        #self.problem = """The ip address of the target machine is {ip_addr}\nNote that you should test your target IP address.\nFinal Goal : {vul_target}\n"""
        self.history = []
        self.commands = []
        self.pname = pname
        self.config = config

    async def agent_state(self, state: AgentState, agent, tools, sname: str) -> dict:
        if sname == 'Exploit':
            max_iterations = self.config['psm']['exp_iterations']
        elif sname == 'Inquire':
            max_iterations = self.config['psm']['query_iterations']
        else:
            max_iterations = self.config['psm']['scan_iterations']
        _executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=max_iterations, return_intermediate_steps=True)

        # --- INSERISCI IL DEBUG QUI ---
        print("\n" + "="*20 + " DEBUG INFO " + "="*20)
        print(f"Stato attuale: {sname}")
        print("Input che verrà passato all'agente (self.problem):")
        print(repr(self.problem)) # Usiamo repr() per vedere anche caratteri speciali come \n
        print("="*52 + "\n")
        # -----------------------------

        result = await _executor.ainvoke({"input": self.problem})
        # 将真正的message清洗出来
        message_str = ''
        history_str = []
        if [] != result['intermediate_steps']:
            for i in result['intermediate_steps']:
                tool_name = i[0].tool
                tool_input = i[0].tool_input
                tool_output = i[1]
                agent_output = i[0].log
                history_str.append(agent_output + str(tool_output))
                message_str += agent_output + str(tool_output)
            message = AIMessage(message_str)
            self.history = self.history + history_str
            self.commands.append(tool_input)
            if sname == 'Inquire' and len(state["vulns"]) > 0:
                state["vulns"][0]['information'] = str(tool_output)
                self.problem += f"Information: " + state["vulns"][0]['information'] + "\n"
        else:
            message = AIMessage(result['output'])
            self.history = self.history + [result['output']]

        return {
            "message": [message],
            "sender": sname,
            # "history": state["history"] + [message],
            "vulns": state["vulns"],
            "check_count": state["check_count"]
        }

    def check_state(self, state: AgentState, name: str = "Check") -> dict:
        print("\n" + "="*20 + " DEBUG STATE " + "="*20)
        print("ENTRATO IN: Check State")
        print("="*53 + "\n")
        check1, check_count = check_str(self.problem, state["message"], state["check_count"], self.pname)
        if check1 == 0:
            check_message = f"Successfully exploited the vulnerability, a total of {check_count} steps were attempted"
        elif check1 in [1, 2]:
            check_message = f"Failed to exploit the vulnerability, please try again. {self.problem}"
        else:
            if len(state["vulns"]) > 1:
                check_message = f"Failed to exploit the vulnerability, please try another vulnerability."
            else:
                check_message = f"Failed to exploit the vulnerability."
        message = HumanMessage(content=check_message)
        self.history = self.history + [check_message]
        return {
            "message": [message],
            "sender": name,
            "vulns": state["vulns"],
            "check_count": check_count
        }

    def vuln_select_state(self, state: AgentState, name: str = "Vuln_select") -> dict:
        print("\n" + "="*20 + " DEBUG STATE " + "="*20)
        print("ENTRATO IN: Vuln Select State")
        print("="*53 + "\n")
        next_prompt = "Your main goal is to use the provided tools to exploit the vulnerabilities in the target system based on the vulnerability information and ultimately achieve the final goal."
        if state['check_count'] == 0:
            scan_res = state["message"][-1]
            vulns = parse_vuln(scan_res.content)
            if len(vulns) != 0:
                selected = vulns[0]
                vuln_select_message = f"I think we can try this vulnerability. The vulnerability information is as follows {selected}"
            else:
                vuln_select_message = f"continue to select vulnerability"
        else:
            vulns = state["vulns"]
            if len(vulns) > 1:
                vulns.pop(0)
            selected = vulns[0]
            vuln_select_message = f"I think we can try this vulnerability. The vulnerability information is as follows {selected}"
        # in modo che il prossimo stato (Inquire) sappia su cosa lavorare.
        if 'selected' in locals() and selected:
            self.problem += f"\n\nSelected Vulnerability Information:\n{str(selected)}"

        message = HumanMessage(content=vuln_select_message)
        self.history = self.history + [vuln_select_message]
        return {
            "message": [message],
            "sender": name,
            "vulns": vulns,
            "check_count": state["check_count"]
        }

    def refresh(self):
        #self.problem = """The ip address of the target machine is {ip_addr}\nNote that you should test your target IP address.\nFinal Goal : {vul_target}\n"""
        self.history = []
        self.commands = []