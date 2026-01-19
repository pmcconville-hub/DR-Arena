# core/agents.py

import time
from core.api_client import call_api_with_retry
from core.utils import parse_citations
from core.tracker import global_token_tracker

class SearchAgent:
    def __init__(self, name, model_config):
        self.name = name
        self.model_config = model_config
        self.system_prompt = "You are a real-time research assistant with access to web search capabilities."
    def research(self, question, word_limit_instruction, history=None):
        start_time = time.time()
        global_token_tracker.add_text(question)
        if history: global_token_tracker.add_text(str(history))
        history_str = ""
        if history:
            history_str = "This is a follow-up question. Context History:\n"
            for msg in history:
                role = "User" if msg['role'] == 'user_question' else "You"
                history_str += f"{role}: {msg['content']}\n"
            history_str += "\n--- END OF HISTORY ---\n"

        prompt_text = f"""
        **Your Task:**  Provide a comprehensive answer using EXTERNAL SEARCH tools.
        **MANDATORY SEARCH:** You MUST perform a fresh web search for this specific question. Do NOT answer based solely on your internal training data or memory.
        **SILENT EXECUTION (EXTREMELY IMPORTANT):** - Perform all search actions, reasoning, and verification **INTERNALLY**. Do not output these contents.

        {history_str}
        **Current Question:** "{question}"
        **Constraint:** {word_limit_instruction} (Note: This word limit applies to the **BODY text only**, excluding the reference list).
        
        **Output Guidelines (CRITICAL):**
        1. **DIRECT ANSWER ONLY:** Start your response immediately with the answer. **Do NOT** output "Thinking Process", "Search Strategy", "I will search for...", "Based on the search results...", or any internal reasoning logs.
        2. **NO FILLER:** Do not start with "Here is the information" or "I found the following". Jump straight into the facts.
        3. **Strict Length Control:** You MUST strictly adhere to the word limit for the **main body** of your response.
        4. **Mandatory References:** You MUST include a reference list at the end.
        
        **Citation Rules:**
        1. Inline: [1], [2] after facts.
        2. Bottom: ## References list.
        Start researching.
        """
        messages = [
            {"role": "system", "content": self.system_prompt}, 
            {"role": "user", "content": prompt_text}
        ]

        global_token_tracker.add_text(self.system_prompt + prompt_text)
        raw_response = call_api_with_retry(self.model_config, messages, max_tokens=4096, temperature=0.2)
        global_token_tracker.add_text(raw_response)
        duration = time.time() - start_time
        if not raw_response:
            return {"final_answer": "Error: No response from API."}, [], duration
        trajectory = {
            "final_answer": raw_response.strip()
        }
        stats = parse_citations(trajectory['final_answer'])
        trajectory['citation_stats'] = stats
        trajectory['sources_consulted'] = stats['unique_sources']
        history_messages = [
            {"role": "user_question", "content": question},
            {"role": "assistant", "content": trajectory['final_answer']}
        ]
        return trajectory, history_messages, duration