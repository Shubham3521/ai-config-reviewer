import os
from github import Github

def open_pull_request(file_path, new_content, commit_message="AI fix"):
    """
    Creates a new branch, commits the fixed YAML, and opens a pull request.
    Requires a GitHub token with repo:write permission.
    """
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO", "Shubham3521/ai-config-reviewer")
    base_branch = os.getenv("GITHUB_BASE", "main")

    if not token:
        raise ValueError("❌ GITHUB_TOKEN not set in environment")

    g = Github(token)
    repo = g.get_repo(repo_name)
    branch_name = f"ai-fix-{os.path.basename(file_path).replace('.', '-')}"
    base = repo.get_branch(base_branch)

    # create branch from base
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base.commit.sha)

    # commit new content
    contents = repo.get_contents(file_path, ref=branch_name)
    repo.update_file(
        path=file_path,
        message=commit_message,
        content=new_content,
        sha=contents.sha,
        branch=branch_name,
    )

    # open PR
    pr = repo.create_pull(
        title=f"AI Suggested Fix: {os.path.basename(file_path)}",
        body="Automatically generated fix by AI Config Reviewer (LangChain).",
        head=branch_name,
        base=base_branch,
    )

    print(f"✅ Pull request created: {pr.html_url}")
    return pr.html_url

