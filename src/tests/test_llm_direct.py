import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from llm_client import LLMGenerator

def main():
    llm = LLMGenerator()
    ctx = [{"content": "浙江大学的前身求是书院创立于1897年"}]
    res = llm.generate_answer("浙江大学什么时候成立的？", ctx, stream=False)
    print(res)

if __name__ == "__main__":
    main()
