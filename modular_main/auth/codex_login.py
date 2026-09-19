"""
A class for managing codex login, using either API key or with a chatgpt account
Access the auth_url for chatgpt login, and use the wait() method to wait for the login to be completed. 
"""

from openai_codex import Codex

class CodexLogin:
    def __init__(self, method="chatgpt", api_key=None):
        self._codex = Codex()
        self._codex.__enter__()
        self.method = method
        self.auth_url = None
        self._login = None

        if method == "api":
            if not api_key:
                raise ValueError("api_key is required for method='api_key'")
            self._codex.login_api_key(api_key)
        else:
            self._login = self._codex.login_chatgpt()
            self.auth_url = self._login.auth_url

    def wait(self):
        try:
            if self.method == "api":
                return True  # already authenticated in __init__
            return self._login.wait()
        finally:
            self._codex.__exit__(None, None, None)

