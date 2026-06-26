from .settings import AGENT, MODEL
from .auth.codex_login import codex_login_gpt_subscription

def login(): 
    if AGENT == "codex": 
        codex_login_gpt_subscription() 

# usage: login.py
if __name__ == "__main__": 
    login() 