import os
import json
from typing import List, Dict
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class LLMGenerator:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.client = None
        self._setup_client()

    def _load_config(self) -> Dict:
        default_config = {
            "llm": {
                "provider": "openai",
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    if "llm" in user_config:
                        default_config["llm"].update(user_config["llm"])
                    return default_config
            except Exception as e:
                print(f"[Error] Error loading config: {e}")
        return default_config

    def _setup_client(self):
        if OpenAI is None:
            print("[Error] OpenAI library not installed. Please install it: pip install openai")
            return
        llm_config = self.config.get("llm", {})
        api_key = llm_config.get("api_key")
        base_url = llm_config.get("base_url")
        provider = llm_config.get("provider", "openai")
        if base_url and "localhost" in base_url:
            base_url = base_url.replace("localhost", "127.0.0.1")
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
        if provider == "ollama" and not api_key:
            api_key = "ollama"
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            print("[WARN] No valid API key found. LLM features will be disabled until configured.")
            return
        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            print(f"[INFO] LLM Client initialized (Model: {llm_config.get('model')})")
        except Exception as e:
            print(f"[ERROR] Failed to initialize LLM Client: {e}")

    def generate_answer(self, query: str, context_chunks: List[Dict], stream: bool = False):
        context_text = "\n\n".join([
            f"--- Document {i+1} ---\n{chunk.get('content', '')}" 
            for i, chunk in enumerate(context_chunks)
        ])
        system_prompt = """你是一个浙江大学校史专家助手。请基于提供的上下文信息回答用户的问题。
        
        要求：
        1. 仅依据提供的上下文回答，不要编造信息。
        2. 如果上下文中没有相关信息，请明确说明"根据现有资料无法回答"。
        3. 回答要条理清晰，语言流畅，准确引用历史事实（如时间、人物、地点）。
        4. 如果有多个相关事件，请按时间顺序组织回答。
        5. 语气要专业、客观、敬业。
        """
        user_prompt = f"""
        问题：{query}

        参考资料：
        {context_text}

        请根据参考资料回答上述问题：
        """
        llm_config = self.config.get("llm", {})
        model = llm_config.get("model", "gpt-3.5-turbo")
        temperature = llm_config.get("temperature", 0.7)
        max_tokens = llm_config.get("max_tokens", 1000)
        if not stream:
            if not self.client:
                return "⚠️ LLM Client not initialized. Please configure API key in config.json."
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"❌ Error generating answer: {e}"
        else:
            def _stream():
                if not self.client:
                    yield "⚠️ LLM Client not initialized. Please configure API key in config.json."
                    return
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True
                    )
                    for chunk in response:
                        if hasattr(chunk.choices[0], "delta") and chunk.choices[0].delta and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                        elif hasattr(chunk.choices[0], "message") and chunk.choices[0].message and chunk.choices[0].message.get("content"):
                            yield chunk.choices[0].message["content"]
                except Exception as e:
                    yield f"❌ Error generating answer: {e}"
            return _stream()
