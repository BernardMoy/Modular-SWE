from openai_codex import Codex

def codex_login_gpt_subscription(): 
    with Codex() as codex:
        login = codex.login_chatgpt()
        print(login.auth_url)
        print(f"Logged in: {login.wait().success}")
