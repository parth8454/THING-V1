import os
import asyncio
from github import Github
from config import GITHUB_TOKEN
from github.GithubException import GithubException

def get_gh_client():
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not set in config.py")
    return Github(GITHUB_TOKEN)

async def create_github_repo(repo_name: str, description: str = "", private: bool = True) -> str:
    """Create a new GitHub repository under the authenticated user's account."""
    def _create():
        g = get_gh_client()
        user = g.get_user()
        repo = user.create_repo(name=repo_name, description=description, private=private)
        return f"Repo '{repo.full_name}' created. URL: {repo.html_url}"
    
    try:
        return await asyncio.to_thread(_create)
    except GithubException as e:
        return f"Repo creation failed: {e.data.get('message', str(e))}"

async def create_or_update_file(repo_name: str, file_path: str, content: str, commit_message: str) -> str:
    """Create or update a file in the specified GitHub repository."""
    def _commit():
        g = get_gh_client()
        repo = g.get_user().get_repo(repo_name)
        try:
        # Agar file pehle se hai toh update    
            file = repo.get_contents(file_path)
            repo.update_file(file.path, commit_message, content, file.sha)
            return f"File '{file_path}' updated in repo '{repo_name}'."
        except GithubException as e:
            if e.status == 404:
                # File nahi mili, matlab naya banana hai
                repo.create_file(file_path, commit_message, content)
                return f"New file '{file_path}' created in repo '{repo_name}'."
            return f"Commit failed: {e.data.get('message', str(e))}"
    
    try:
        return await asyncio.to_thread(_commit)
    except Exception as e:
        return f"Error: {str(e)}"

async def get_file_content(repo_name: str, file_path: str) -> str:
    """Fetch the content of a file from the specified GitHub repository."""
    def _get():
        g = get_gh_client()
        repo = g.get_user().get_repo(repo_name)
        file = repo.get_contents(file_path)
        return file.decoded_content.decode("utf-8")
    
    try:
        return await asyncio.to_thread(_get)
    except GithubException as e:
        return f"Failed to fetch file content: {e.data.get('message', str(e))}"


# ------------------------------------------------------------------------------------------

# Add these functions to capabilities/github_tools.py

async def list_repos() -> str:
    """List all GitHub repositories of the authenticated user."""
    def _list():
        g = get_gh_client()
        user = g.get_user()
        repos = user.get_repos()
        result = []
        for r in repos:
            result.append(f"- {r.name} ({'private' if r.private else 'public'}) | ⭐ {r.stargazers_count} | {r.description or 'No description'}")
        return "\n".join(result) if result else "No repos found."
    try:
        return await asyncio.to_thread(_list)
    except Exception as e:
        return f"Error: {str(e)}"


async def get_repo_info(repo_name: str) -> str:
    """Get detailed info about a GitHub repository — stars, forks, issues, branches, last commit."""
    def _info():
        g = get_gh_client()
        repo = g.get_user().get_repo(repo_name)
        last_commit = repo.get_commits()[0]
        return (
            f"Repo: {repo.full_name}\n"
            f"Description: {repo.description or 'None'}\n"
            f"Stars: {repo.stargazers_count}\n"
            f"Forks: {repo.forks_count}\n"
            f"Open Issues: {repo.open_issues_count}\n"
            f"Default Branch: {repo.default_branch}\n"
            f"Last Commit: {last_commit.commit.message[:80]} by {last_commit.commit.author.name}\n"
            f"URL: {repo.html_url}"
        )
    try:
        return await asyncio.to_thread(_info)
    except Exception as e:
        return f"Error: {str(e)}"


async def create_branch(repo_name: str, branch_name: str, from_branch: str = "main") -> str:
    """Create a new branch in a GitHub repository."""
    def _branch():
        g = get_gh_client()
        repo = g.get_user().get_repo(repo_name)
        source = repo.get_branch(from_branch)
        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=source.commit.sha
        )
        return f"Branch '{branch_name}' created from '{from_branch}' in '{repo_name}'."
    try:
        return await asyncio.to_thread(_branch)
    except Exception as e:
        return f"Error: {str(e)}"


async def create_pull_request(repo_name: str, title: str, body: str, head_branch: str, base_branch: str = "main") -> str:
    """Create a pull request in a GitHub repository."""
    def _pr():
        g = get_gh_client()
        repo = g.get_user().get_repo(repo_name)
        pr = repo.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base_branch
        )
        return f"PR created: {pr.html_url}"
    try:
        return await asyncio.to_thread(_pr)
    except Exception as e:
        return f"Error: {str(e)}"


async def commit_file(repo_name: str, file_path: str, content: str, commit_message: str, branch: str = "main") -> str:
    """Commit a file to a specific branch in a GitHub repository."""
    def _commit():
        g = get_gh_client()
        repo = g.get_user().get_repo(repo_name)
        try:
            existing = repo.get_contents(file_path, ref=branch)
            repo.update_file(
                existing.path,
                commit_message,
                content,
                existing.sha,
                branch=branch
            )
            return f"File '{file_path}' updated on branch '{branch}' in '{repo_name}'."
        except Exception as e:
            if "404" in str(e):
                repo.create_file(file_path, commit_message, content, branch=branch)
                return f"File '{file_path}' created on branch '{branch}' in '{repo_name}'."
            return f"Error: {str(e)}"
    try:
        return await asyncio.to_thread(_commit)
    except Exception as e:
        return f"Error: {str(e)}"