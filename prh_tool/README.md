# PRH Tool

Test additional details
This tool automates the process of creating a Pull Request on GitHub.

## Features

- Stages all changes (`git add .`)
- Prompts for a commit message with suggestions (`git commit -m`)
- Pushes changes to the remote repository (`git push origin <branch_name>`)
- Creates a Pull Request on GitHub using the GitHub API

## Setup

No manual setup is required for dependencies or environment variables. The tool will automatically install the `requests` library if needed and prompt you for your GitHub Personal Access Token if it's not already set as an environment variable.

## Usage

1.  Navigate to your repository directory in the terminal.
2.  Make your code changes.
3.  Run the `prh.py` script:
    ```bash
    python prh_tool/prh.py
    ```
4.  Follow the prompts to enter your GitHub Personal Access Token (if asked), commit message, PR title, and PR body.

The tool will then stage, commit, push your changes, and create a Pull Request on GitHub.
