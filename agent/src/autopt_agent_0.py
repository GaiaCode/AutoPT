import argparse
from react_agent import run_react

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://juiceshop:3000", help="Base URL to test")
    p.add_argument("--allow-posts", action="store_true", help="Allow harmless POST requests if forms detected")
    p.add_argument("--seed", type=int, default=0, help="Random seed for mock LLM reproducibility")
    args = p.parse_args()
    run_react(base_url=args.base_url, allow_posts=args.allow_posts, seed=args.seed)
