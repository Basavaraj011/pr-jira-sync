from .bitbucket import BitbucketProvider
from .github_connections import GitHubProvider


def get_provider(kind: str):
    if kind == "bitbucket":
        from config.settings import BITBUCKET_REPO_SLUG,BITBUCKET_API_USERNAME, BITBUCKET_AUTH_TOKEN, BITBUCKET_GIT_USERNAME, BITBUCKET_URL, BITBUCKET_WORKSPACE
        return BitbucketProvider(
            workspace=BITBUCKET_WORKSPACE,
            repo_slug=BITBUCKET_REPO_SLUG,
            api_username=BITBUCKET_API_USERNAME,
            git_username=BITBUCKET_GIT_USERNAME,
            app_password=BITBUCKET_AUTH_TOKEN,
            reviewers=[],
            url = BITBUCKET_URL
        )
    if kind == "git":
        from config.settings import GIT_OWNER, GIT_REPO, GIT_TOKEN
        return GitHubProvider(
            owner = GIT_OWNER,
            repo = GIT_REPO,
            token = GIT_TOKEN
        )
    raise ValueError(f"Unsupported provider: {kind}")