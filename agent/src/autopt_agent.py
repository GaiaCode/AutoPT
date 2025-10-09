from llm_client import LLMClient
from environment import Environment

def main():
    env = Environment()
    llm = LLMClient()
    print("[*] AutoPT agent started (dry run)")
    obs = env.get_page("http://juiceshop:3000")
    print(obs[:500])

if __name__ == "__main__":
    main()
