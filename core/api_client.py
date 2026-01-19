# core/api_client.py

import time
import logging
from openai import OpenAI
from config import OPENROUTER_API_KEY, API_MAX_RETRY, API_RETRY_SLEEP

client = OpenAI(
    base_url="your_url_here",
    api_key=OPENROUTER_API_KEY,
    timeout=500.0, 
    default_headers={
        "HTTP-Referer": "", 
        "X-Title": "",
    },
)

def call_api_with_retry(model_config, messages, **kwargs):
    model_id = model_config['id']
    supported_params = model_config.get('supported_params', ['max_tokens'])
    api_kwargs = {key: value for key, value in kwargs.items() if key in supported_params}
    
    for i in range(API_MAX_RETRY):
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                **api_kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.warning(f"API call for {model_id} failed: {e}. Retrying ({i+1}/{API_MAX_RETRY})...")
            if i == API_MAX_RETRY - 1:
                logging.error(f"API call for {model_id} failed after retries.")
                return None
            time.sleep(API_RETRY_SLEEP)
    return None