# config.py

# --- API Key & Retry Strategy ---
OPENROUTER_API_KEY = "your_api_key_here"
API_MAX_RETRY = 3
API_RETRY_SLEEP = 20

# --- Model Configurations ---

# Models to be tested
AVAILABLE_SEARCH_MODELS = {
    "grok-4-fast-search": {
        "id": "x-ai/grok-4-fast",
        "supported_params": [] 
    },
    "gemini-2.5-pro-grounding": {
        "id": "google/gemini-2.5-pro",
        "supported_params": [] 
    },    
    "o3-search": {
        "id": "openai/o3",
        "supported_params": [] 
    },
    "grok-4-search": {
        "id": "x-ai/grok-4",
        "supported_params": [] 
    }, 
    "ppl-sonar-pro-high": {
        "id": "perplexity/sonar-pro",
        "supported_params": []
    },
    "gpt-5.1-search": {
        "id": "openai/gpt-5.1",
        "supported_params": [] 
    },
    "gpt-5-search": {
        "id": "openai/gpt-5",
        "supported_params": [] 
    },
    "claude-opus-4-search": {
        "id": "anthropic/claude-opus-4",
        "supported_params": [] 
    },
    "claude-opus-4-1-search": {
        "id": "anthropic/claude-opus-4.1",
        "supported_params": [] 
    },
     "ppl-sonar-reasoning-pro-high": {
        "id": "perplexity/sonar-reasoning-pro",
        "supported_params": []
    },
    #Deep Research
    "tongyi-deep-research": {
        "id": "alibaba/tongyi-deepresearch-30b-a3b:free",
        "supported_params": ["temperature", "max_tokens"]
    },
    "sonar-deep-research": {
        "id": "perplexity/sonar-deep-research",
        "supported_params": ["temperature", "max_tokens"]
    },
    "api-gpt-4o-search": {
        "id": "openai/gpt-4o-search-preview",
        "supported_params": [] 
    },
    "gpt4o-mini-search": {
        "id": "openai/gpt-4o-mini-search-preview",
        "supported_params": [] 
    },
    "o3-deep-research": {
        "id": "openai/o3-deep-research",
        "supported_params": [] 
    },       
}

TASK_GENERATOR_MODEL_CONFIG = {
    "id": "google/gemini-3-pro-preview",
    "supported_params": ["temperature"]
}
# Hyperparameters
MIN_ROUNDS = 1
MAX_ROUNDS = 10
WIN_THRESHOLD = 2.0
ESTIMATED_COST_PER_1M_TOKENS = 10.0