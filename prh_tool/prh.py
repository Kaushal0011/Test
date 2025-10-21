import subprocess
import os
import sys

try:
    import requests
except ImportError:
    print("'requests' library not found. Installing now...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
        print("'requests' installed successfully.")
    except Exception as e:
        print(f"Failed to install 'requests' library: {e}")
        sys.exit(1)

def run_command(command):
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        return result.stdout  # Return stdout on success
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return None # Return None on failure

def stage_changes():
    print("Staging all changes...")
    status_output = run_command(["git", "status", "--porcelain"])
    if status_output is None:
        print("Failed to get git status. Aborting staging.")
        return False

    if not status_output.strip():
        print("No changes to stage.")
        return True # No changes to stage, but not an error

    if run_command(["git", "add", "."]) is None:
        print("Failed to stage changes.")
        return False
    return True

def commit_changes():
    # Check if there are any staged changes before prompting for a commit message
    diff_cached_output = run_command(["git", "diff", "--cached"])
    if diff_cached_output is None:
        print("Failed to get staged changes. Aborting commit.")
        return False

    if not diff_cached_output.strip():
        print("No staged changes to commit.")
        return True # No changes to commit, but not an error

    suggestions = [
        "feat: Add new feature",
        "fix: Resolve bug",
        "docs: Update documentation",
        "refactor: Refactor code",
        "style: Apply code style",
        "test: Add or update tests",
        "chore: Minor changes"
    ]
    print("\nSuggested commit message types:")
    for i, suggestion in enumerate(suggestions):
        print(f"  {i+1}. {suggestion}")

    commit_message = input("Enter your commit message: ")
    if not commit_message:
        print("Commit message cannot be empty. Aborting commit.")
        return False
    print(f"Committing with message: '{commit_message}'")
    if run_command(["git", "commit", "-m", commit_message]) is None:
        print("Failed to commit changes.")
        return False
    return True

def get_current_branch():
    branch_name = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch_name is not None:
        return branch_name.strip()
    return None

def push_changes():
    branch_name = get_current_branch()
    if not branch_name:
        print("Could not determine current branch. Aborting push.")
        return False

    print(f"Pushing changes to origin/{branch_name}...")
    if run_command(["git", "push", "origin", branch_name]) is None:
        print("Failed to push changes.")
        return False
    return True

def get_github_repo_info():
    remote_url = run_command(["git", "config", "--get", "remote.origin.url"])
    if remote_url is None:
        print("Could not get remote origin URL.")
        return None, None
    
    # Need to re-run the command to get stdout
    result = subprocess.run(["git", "config", "--get", "remote.origin.url"], check=True, capture_output=True, text=True)
    remote_url = result.stdout

    # Handle both HTTPS and SSH URLs
    if "https://github.com/" in remote_url:
        parts = remote_url.strip().split('/')
        owner = parts[-2]
        repo = parts[-1].replace(".git", "")
    elif "git@github.com:" in remote_url:
        parts = remote_url.strip().split(':')
        owner_repo = parts[-1].replace(".git", "").split('/')
        owner = owner_repo[0]
        repo = owner_repo[1]
    else:
        print(f"Unsupported remote URL format: {remote_url}")
        return None, None

    return owner, repo

def create_pull_request(title, body, head_branch):
    owner, repo = get_github_repo_info()
    if not owner or not repo:
        return False

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        github_token = input("GITHUB_TOKEN environment variable not set. Please enter your GitHub Personal Access Token: ")
        if not github_token:
            print("GitHub Personal Access Token cannot be empty. Aborting PR creation.")
            return False

    # Get the default branch of the repository
    repo_info_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(repo_info_url, headers=headers)
    if response.status_code == 200:
        repo_data = response.json()
        base_branch = repo_data.get("default_branch", "main") # Fallback to 'main' if not found
        print(f"Determined base branch: {base_branch}")
    else:
        print(f"Failed to get repository info to determine default branch: {response.status_code}")
        print(response.json())
        base_branch = "main" # Default to main if unable to fetch
        print(f"Defaulting to base branch: {base_branch}")

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch
    }

    print(f"Creating pull request for {owner}/{repo} from {head_branch} to {base_branch}...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        print(f"Pull Request created successfully: {response.json()['html_url']}")
        return True
    else:
        print(f"Failed to create Pull Request: {response.status_code}")
        print(response.json())
        return False


if __name__ == "__main__":
    if stage_changes():
        if commit_changes():
            if push_changes():
                # Placeholder for PR title and body - will need to be made dynamic
                current_branch = get_current_branch()
                if current_branch:
                    pr_title = input("Enter Pull Request title: ")
                    pr_body = input("Enter Pull Request body (optional): ")
                    create_pull_request(pr_title, pr_body, current_branch)
