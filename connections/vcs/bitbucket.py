import os
import subprocess
from pathlib import Path
from urllib.parse import quote
import requests
from connections.vcs.provider import VCSProvider
from config.settings import BITBUCKET_WORKSPACE, BITBUCKET_URL, BITBUCKET_REPO_SLUG, BITBUCKET_API_USERNAME, BITBUCKET_APP_PASSWORD, BITBUCKET_GIT_USERNAME, BITBUCKET_REVIEWERS

class BitbucketProvider(VCSProvider):
    """
    Provider used by open_pr(), supporting dual-identity Bitbucket auth:
    - Git operations use Bitbucket ACCOUNT USERNAME.
    - REST API operations use EMAIL (because your account authenticates that way).
    """


    def __init__(self,workspace, repo_slug, api_username, git_username, app_password, reviewers, url):
        self.workspace = workspace
        self.repo_slug = repo_slug

        self.api_username = api_username
        self.git_username = git_username or api_username
        self.app_password = app_password
        self.reviewers = reviewers or []

        self.base_url = url.rstrip("/") if (url := url) else BITBUCKET_URL.rstrip("/")

        # REST API BASIC AUTH — uses EMAIL
        self.session = requests.Session()
        self.session.auth = (self.api_username, self.app_password)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        
        })
        print(f"Initialized BitbucketProvider with API username: {self.api_username} and Git username: {self.git_username}")

    # ---------------------------------------------------------------
    # Git Operations (uses account username)
    # ---------------------------------------------------------------

    
    def clone_repo(self) -> str:

        base_tmp = os.getenv("TMPDIR") or os.getenv("TEMP") or os.getenv("TMP") or "/tmp"
        tmp = Path(base_tmp) / f"selfheal_bb_{os.urandom(4).hex()}"
        tmp.mkdir(parents=True, exist_ok=True)

        # Ensure values are STR before quoting
        user = quote(str(self.git_username), safe="")
        pwd  = quote(str(self.app_password), safe="")

        clone_url = f"https://{user}:{pwd}@bitbucket.org/{self.workspace}/{self.repo_slug}.git"
        print(f"Cloning repository from https://***:***@bitbucket.org/{self.workspace}/{self.repo_slug}.git to {tmp}...")
        # Disable credential helper so Windows GCM does not override embedded URL credentials
        subprocess.check_call(
            ["git", "-c", "credential.helper=", "clone", clone_url, str(tmp)],
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        return str(tmp)

    def _run_git(self, repo_dir, *args):
        try:
            return subprocess.check_output(
                args,
                cwd=repo_dir,
                text=True,
                stderr=subprocess.PIPE,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            ).strip()
        except subprocess.CalledProcessError as e:
            print(f"[GIT ERROR] command: {e.cmd}")
            print(f"[GIT ERROR] stderr:\n{e.stderr}")
            print(f"[GIT ERROR] stdout:\n{e.output}")
            raise subprocess.CalledProcessError(e.returncode, e.cmd, e.output, e.stderr) from e

    def create_branch(self, repo_dir, branch, base="main"):
        self._run_git(repo_dir, "git", "fetch", "origin", base)
        self._run_git(repo_dir, "git", "checkout", "-B", branch, f"origin/{base}")

    def commit_and_push(self, repo_dir, message, branch):
        self._run_git(repo_dir, "git", "add", "-A")

        try:
            self._run_git(
                repo_dir,
                "git",
                "-c", "user.name=Self-Heal Bot",
                "-c", "user.email=selfheal-bot@local",
                "commit",
                "-m", message,
            )
        except subprocess.CalledProcessError:
            raise RuntimeError("Nothing to commit")

        from urllib.parse import quote as _quote
        user = _quote(str(self.git_username), safe="")
        pwd  = _quote(str(self.app_password), safe="")
        push_url = f"https://{user}:{pwd}@bitbucket.org/{self.workspace}/{self.repo_slug}.git"
        print(f"[GIT PUSH] git_username in provider: {self.git_username}")
        print(f"[GIT PUSH] app_password set: {bool(self.app_password)}")
        self._run_git(repo_dir, "git", "-c", "credential.helper=", "push", "-u", push_url, branch)
        return self._run_git(repo_dir, "git", "rev-parse", "HEAD")

    # ---------------------------------------------------------------
    # PR Creation — uses REST API (email)
    # ---------------------------------------------------------------
    def create_pull_request(self, title, body_md, source_branch, dest_branch="main", draft=False):
        url = (
            f"{self.base_url}/repositories/"
            f"{self.workspace}/{self.repo_slug}/pullrequests"
        )

        reviewers = [{"uuid": r} for r in (self.reviewers or [])]

        payload = {
            "title": title,
            "summary": {"raw": body_md},
            "source": {"branch": {"name": source_branch}},
            "destination": {"branch": {"name": dest_branch}},
            "reviewers": reviewers,
            "close_source_branch": False,
            "draft": draft,
        }

        response = self.session.post(url, json=payload)

        if response.status_code >= 300:
            raise RuntimeError(
                f"PR create failed: {response.status_code}\n{response.text}"
            )

        return response.json()
    
if __name__ == "__main__":
    provider = BitbucketProvider()
    repo_dir = provider.clone_repo()
    print(f"Repository cloned to: {repo_dir}")