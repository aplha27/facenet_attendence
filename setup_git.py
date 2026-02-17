#!/usr/bin/env python3
"""
Setup Git repository and prepare for version control
"""

import os
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(cmd, check=True):
    """Run a shell command"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_git_installed():
    """Check if git is installed"""
    success, stdout, stderr = run_command("git --version", check=False)
    if success:
        logger.info(f"✓ Git is installed: {stdout.strip()}")
        return True
    else:
        logger.error("✗ Git is not installed")
        logger.info("Please install Git from: https://git-scm.com/downloads")
        return False

def initialize_git():
    """Initialize git repository"""
    if Path(".git").exists():
        logger.info("✓ Git repository already initialized")
        return True
    
    logger.info("Initializing Git repository...")
    success, stdout, stderr = run_command("git init")
    
    if success:
        logger.info("✓ Git repository initialized")
        return True
    else:
        logger.error(f"✗ Failed to initialize Git: {stderr}")
        return False

def create_gitignore():
    """Ensure .gitignore exists"""
    if Path(".gitignore").exists():
        logger.info("✓ .gitignore already exists")
        return True
    
    logger.warning("✗ .gitignore not found")
    return False

def add_files():
    """Add files to git"""
    logger.info("Adding files to Git...")
    
    # Add all files
    success, stdout, stderr = run_command("git add .")
    
    if success:
        logger.info("✓ Files added to Git")
        return True
    else:
        logger.error(f"✗ Failed to add files: {stderr}")
        return False

def create_initial_commit():
    """Create initial commit"""
    logger.info("Creating initial commit...")
    
    # Check if there are changes to commit
    success, stdout, stderr = run_command("git status --porcelain")
    
    if not stdout.strip():
        logger.info("✓ No changes to commit (repository is clean)")
        return True
    
    # Create commit
    commit_message = "Initial commit: Modernized FaceNet Attendance System"
    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    
    if success:
        logger.info(f"✓ Initial commit created: {commit_message}")
        return True
    else:
        logger.error(f"✗ Failed to create commit: {stderr}")
        return False

def configure_git_user():
    """Configure git user if not set"""
    # Check if user.name is set
    success, stdout, stderr = run_command("git config user.name", check=False)
    
    if not stdout.strip():
        logger.warning("Git user.name not configured")
        logger.info("Please configure with: git config --global user.name \"Your Name\"")
        return False
    
    # Check if user.email is set
    success, stdout, stderr = run_command("git config user.email", check=False)
    
    if not stdout.strip():
        logger.warning("Git user.email not configured")
        logger.info("Please configure with: git config --global user.email \"your.email@example.com\"")
        return False
    
    logger.info(f"✓ Git user configured: {stdout.strip()}")
    return True

def show_git_status():
    """Show current git status"""
    logger.info("\nCurrent Git Status:")
    logger.info("=" * 50)
    
    success, stdout, stderr = run_command("git status")
    
    if success:
        print(stdout)
    else:
        logger.error(f"Failed to get status: {stderr}")

def create_readme_for_git():
    """Create a simple README for Git"""
    readme_content = """# Git Setup Complete!

## Repository Status
Your project is now Git-ready and version controlled.

## Next Steps

### 1. Configure Git (if not done)
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 2. Check Status
```bash
git status
```

### 3. Make Changes and Commit
```bash
# After making changes
git add .
git commit -m "Your commit message"
```

### 4. Create Remote Repository
1. Create a new repository on GitHub/GitLab/Bitbucket
2. Add remote:
```bash
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```

## Useful Git Commands

### View History
```bash
git log
git log --oneline
```

### Create Branch
```bash
git checkout -b feature-name
```

### Switch Branch
```bash
git checkout main
```

### Merge Branch
```bash
git checkout main
git merge feature-name
```

### Pull Changes
```bash
git pull origin main
```

### Push Changes
```bash
git push origin main
```

## Files Ignored by Git
Check `.gitignore` for files that won't be tracked:
- Virtual environments (venv/)
- Database files (*.db)
- Environment files (.env)
- Uploaded files (uploads/)
- Generated reports (reports/)
- Python cache (__pycache__/)
- Model files (*.pkl)

## Important Notes
- Never commit sensitive data (.env files, passwords, API keys)
- Keep your .gitignore up to date
- Write meaningful commit messages
- Commit often, push regularly
"""
    
    with open("GIT_GUIDE.md", "w") as f:
        f.write(readme_content)
    
    logger.info("✓ Created GIT_GUIDE.md")

def main():
    logger.info("Setting up Git repository...")
    logger.info("=" * 50)
    
    # Check if git is installed
    if not check_git_installed():
        return
    
    # Initialize repository
    if not initialize_git():
        return
    
    # Check .gitignore
    if not create_gitignore():
        logger.warning("Please create .gitignore file")
    
    # Configure git user
    user_configured = configure_git_user()
    
    # Add files
    if add_files():
        # Create initial commit (only if user is configured)
        if user_configured:
            create_initial_commit()
        else:
            logger.warning("Skipping commit - please configure Git user first")
    
    # Create Git guide
    create_readme_for_git()
    
    # Show status
    show_git_status()
    
    logger.info("\n" + "=" * 50)
    logger.info("🎉 Git Setup Complete!")
    logger.info("=" * 50)
    logger.info("\nYour project is now version controlled!")
    logger.info("Read GIT_GUIDE.md for next steps")
    
    if not user_configured:
        logger.info("\n⚠️  Don't forget to configure Git user:")
        logger.info('   git config --global user.name "Your Name"')
        logger.info('   git config --global user.email "your.email@example.com"')

if __name__ == "__main__":
    main()