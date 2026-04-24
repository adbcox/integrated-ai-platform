# GitHub Authentication & Push Guide

**Date**: 2026-04-24  
**Status**: Ready to push 69 commits (awaiting user authentication)

---

## Current System State

```
✓ Git repository: /Users/admin/repos/integrated-ai-platform
✓ Remote: https://github.com/adbcox/integrated-ai-platform.git
✓ Commits ready: 69 (68 existing + 1 system repair)
✓ Credential helper: osxkeychain (configured)
✗ Stored credentials: NONE (need token)
```

## Why Credentials Are Needed

When using HTTPS remote URLs with git, you need to authenticate to GitHub. This can be done with:
1. **Personal Access Token (PAT)** - Recommended for scripts and CI/CD
2. **GitHub password** - Less secure, deprecated by GitHub
3. **OAuth via gh CLI** - Most user-friendly

Since SSH key is not registered in GitHub account, HTTPS is the viable option.

---

## Authentication Method 1: GitHub CLI (RECOMMENDED)

**Why**: Simplest, most secure, automatic Keychain storage

```bash
gh auth login
```

**Steps**:
1. **Prompted**: "What is your preferred protocol for Git operations?"
   - Choose: **HTTPS**

2. **Prompted**: "Authenticate Git with your GitHub credentials?"
   - Choose: **Yes**

3. **Prompted**: "How would you like to authenticate GitHub CLI?"
   - Option A: "Login with a web browser" (easiest)
     - Browser opens, you authorize the app
     - Automatic after authorization
   - Option B: "Paste an authentication token"
     - Get token from: https://github.com/settings/tokens/new
     - Paste the token

**After completion**:
```bash
git push origin main
# Should complete without prompting (token stored in Keychain)
```

---

## Authentication Method 2: Manual Personal Access Token

**Why**: More control, useful if gh CLI doesn't work

### Step 1: Create Personal Access Token on GitHub

1. Go to: https://github.com/settings/tokens/new
2. Set **Token name**: `git-credential-osxkeychain`
3. Set **Expiration**: 90 days (or No expiration if preferred)
4. **Select scopes**:
   - ☑ `repo` - Full control of private repositories
   - ☑ `gist` - Create gists
5. Click **Generate token**
6. **COPY THE TOKEN** - You won't see it again after leaving the page
   - Paste it somewhere safe temporarily

### Step 2: Authenticate Git Push

```bash
git push origin main
```

**When prompted**:
```
Username for 'https://github.com': adbcox
Password for 'https://adbcox@github.com': <PASTE_TOKEN_HERE>
```

**Important**: 
- Username: `adbcox`
- Password: The token you copied (NOT your GitHub password)

### Step 3: Token is Saved

After first push, token is automatically saved in macOS Keychain by osxkeychain credential helper.

Future pushes will use stored token automatically.

---

## Troubleshooting

### "Invalid credentials" error
- Make sure you used the **token**, not your GitHub password
- Token is from `https://github.com/settings/tokens/new`

### "Keychain integration failed"
- osxkeychain should be configured:
  ```bash
  git config --global credential.helper osxkeychain
  ```

### "Repository not found" error
- Verify remote URL:
  ```bash
  git remote -v
  # Should show: https://github.com/adbcox/integrated-ai-platform.git
  ```

### Token expires, need to update
- Create new token: https://github.com/settings/tokens/new
- Clear old credentials from Keychain:
  ```bash
  security delete-internet-password -s github.com
  ```
- Try push again, will prompt for new credentials

---

## Verification After Push

After successful authentication and push:

```bash
# Check git status
git status
# Should show: Your branch is up to date with 'origin/main'

# Verify commits on GitHub
git log --oneline -3
# Should match: https://github.com/adbcox/integrated-ai-platform/commits/main
```

---

## Security Notes

1. **Personal Access Tokens**:
   - Treat like passwords - keep secure
   - Can be revoked at any time: https://github.com/settings/tokens
   - Set expiration dates for better security

2. **osxkeychain**:
   - Stores credentials in macOS Keychain
   - Protected by system security
   - Only accessible to your user account

3. **GitHub CLI**:
   - Uses OAuth token internally
   - More secure than storing passwords
   - Automatically handles token refresh

---

## Command Reference

```bash
# Check credential helper configuration
git config --list | grep credential

# Manually store credentials (if needed)
echo "https://adbcox:<TOKEN>@github.com" | git credential approve

# Clear stored credentials
security delete-internet-password -s github.com

# Test HTTPS connectivity
git ls-remote https://github.com/adbcox/integrated-ai-platform.git

# Final push command
git push origin main
```

---

## Status: Ready to Proceed

Once you complete authentication via one of the methods above, run:

```bash
git push origin main
```

This will push all 69 commits to GitHub, making them visible at:
https://github.com/adbcox/integrated-ai-platform

The commit history will show the system repair work and all previous improvements.
