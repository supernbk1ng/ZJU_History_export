import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import json
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""
os.environ["NO_PROXY"] = "*"
from openai import OpenAI
def test_ollama():
    print("Testing Ollama connection...")
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            llm_config = config.get("llm", {})
    except Exception as e:
        print(f"Failed to load config: {e}")
        return
    base_url = llm_config.get("base_url")
    if "localhost" in base_url:
        base_url = base_url.replace("localhost", "127.0.0.1")
        print(f"Adjusted host to 127.0.0.1 for stability")
    api_key = llm_config.get("api_key", "ollama")
    model = llm_config.get("model", "deepseek-r1:latest")
    print(f"Target: {base_url}")
    print(f"Model: {model}")
    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        print("\nChecking available models...")
        try:
            models = client.models.list()
            available_models = [m.id for m in getattr(models, 'data', []) or []]
            print(f"Found {len(available_models)} models.")
        except Exception as e:
            print(f"Failed to list models: {e}")
            available_models = []
        print(f"\nTesting generation with model '{model}'...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "你好，请用一句话介绍浙江大学。"}],
                max_tokens=100
            )
            print(f"Response received:\n{response.choices[0].message.content}")
            print("\nOllama is ready to use!")
        except Exception as e:
            print(f"Generation failed: {e}")
    except Exception as e:
        print(f"\nOllama test failed: {e}")
if __name__ == "__main__":
    test_ollama()
