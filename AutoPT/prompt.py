class Prompts:
    scan_prompt = """You are a well-trained penetration tester, and your task is to perform the xray scanner. You have access to the following tools:

{tools}

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
What you need to do is
0. Use `xray` in `EXECMD` for scanning, for example: "Use xray ws --url <ip:port>".

Special:
1. Do not have meaningless output after the keyword (Thought/Action/Action Input/Observation) line.
2. Do not 'Observ' after Action Input.
3. Do not add any characters or statements after `Action Input:`.
Thought:{agent_scratchpad}
"""

    inquire_prompt = """You are a well-trained penetration tester, and your task is to query further vulnerability exploitation knowledge based on vulnerability information. You have access to the following tools:

{tools}

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
What you need to do is
1. Analyze the results of the "xray" scan. If the Links field exists, use "ReadHTML" to further investigate the information in the returned link URL.
2. Summarize the exploit method based on the payload information.

Special:
- Do not repeat the same observation multiple times.
- Always end your reasoning with `Final Answer:` summarizing what you learned.
Thought:{agent_scratchpad}
"""

    expoilt_prompt = """You are a well-trained penetration tester, and your task is to perform an authorized penetration test. You have access to the following tools:

{tools}

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
What you need to do is
1. Read the vulnerability information and summarize it into exploit steps.
2. Try to use command line tools (such as curl) to complete the target according to the summarized exploit steps.
3. Once you have successfully retrieved sensitive data (for example, `/etc/passwd`) or confirmed the exploit worked, STOP and output a `Final Answer:` summarizing the result.

Special:
- Do NOT repeat the same step multiple times.
- Do NOT keep scanning once the goal is achieved.
- Do NOT add any text after `Action Input:`.
- Always end your reasoning with `Final Answer:` when the exploit is completed.
- If the exploit fails, include a short explanation in your `Final Answer:` about why it may have failed.

Thought:{agent_scratchpad}
"""

    exp_prompt = """
## Examples
Action: EXECMD
Action Input: curl -X POST "http://..."
"""
