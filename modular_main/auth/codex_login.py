from openai_codex import Codex


class CodexLogin:
    def __init__(self):
        self._codex = Codex()
        self._codex.__enter__()
        self._login = self._codex.login_chatgpt()
        self.auth_url = self._login.auth_url

    def wait(self):
        try:
            return self._login.wait()
        finally:
            self._codex.__exit__(None, None, None)
