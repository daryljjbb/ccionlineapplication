GitHub setup and CI runbook for this project

This document lists the steps we performed (and the exact commands) to get the repository working with GitHub and GitHub Actions. Use it as a reference when reproducing the setup on a new machine or repository.

1) Prepare local repo and virtualenv

- Create a Python virtual environment and activate it:
  python -m venv env
  source env/bin/activate

- Install project dependencies (if requirements.txt exists):
  pip install -r requirements.txt

2) Ensure Django app structure

- Confirm your app contains an app-level templatetags package at `webapp/templatetags` with `__init__.py` and custom tag modules (for example `webapp_extras.py`).
- Remove any duplicate templatetag modules from template folders (e.g., `templates/.../templatetags`) — Django discovers tags only from app-level `templatetags` packages.

3) Add the CI workflow file

- Create `.github/workflows/ci.yml` with triggers and steps to install dependencies, run migrations, and run tests. Example used in this repo includes a `workflow_dispatch` manual trigger, a Python matrix, pip cache, and a flake8 lint step.

UI: Where to add a workflow file in GitHub

- Option A (recommended): Push the file in your branch and let GitHub Actions read it. After pushing, you can run it manually or merge it into the default branch.
- Option B: In the GitHub web UI, go to your repo → Actions → New workflow → set up a workflow yourself → commit the created YAML file into a branch.

4) Push branch to GitHub

- Add a remote and push your branch (SSH recommended):
  git remote add origin git@github.com:<your-user>/<your-repo>.git
  git push -u origin BRANCH

- If using HTTPS, create a Personal Access Token (PAT) and use it as the password when pushing.

UI: Add an SSH key to GitHub

1. On your machine, print the public key (default):
   cat ~/.ssh/id_ed25519.pub
2. In GitHub, click your avatar → Settings → SSH and GPG keys → New SSH key.
3. Paste the public key into the "Key" field and give it a Title (e.g., "Workstation").
4. Click "Add SSH key".

UI: Create a Personal Access Token (PAT)

1. In GitHub, click your avatar → Settings → Developer settings → Personal access tokens.
2. Choose: (a) "Tokens (classic)" or (b) "Fine-grained tokens" (recommended for least privilege).
3. Click "Generate new token".
4. Give the token a name, expiry, and select scopes — for repo access include `repo` (or fine-grained: grant the repo and the Actions scopes you need).
5. Click "Generate token" and copy the token value (you won't be able to see it again). Use this as your password when pushing over HTTPS.

5) Trigger CI

- Manual run: go to the repo → Actions tab → choose the workflow on the left → the workflow page lists recent runs and a green "Run workflow" button (if `workflow_dispatch` is enabled). Click it, choose the branch, then click the green "Run workflow" button in the modal.
- Automatic run: merge the branch containing the workflow file into the repository default branch (for example `main`) so Actions will run on future pushes and PRs.

UI: See a workflow run for a specific commit

1. Open your repo → Commits (Code → main → commits) and click the commit you care about.
2. On the commit page you'll see a "checks" section and a link to the Actions run; click it to view logs and job steps.

6) Common troubleshooting

- "'mytag' is not a registered tag library": ensure `templatetags` directory is in the app root and contains `__init__.py` and the tag module. If you see duplicate templatetag files under `templates/.../templatetags`, remove them.
- "Authentication failed" on push: use SSH keys (add to GitHub) or create a PAT for HTTPS.
- Actions lists 0 workflows: GitHub displays workflows from the default branch; either merge the workflow to the default branch or add `workflow_dispatch` and run manually from the branch.

UI: Finding Pull Requests and merging

1. Open your repo → Pull requests (top nav) to see open PRs. If none appear, no PRs exist.
2. To open a new PR from a branch you pushed: go to Pull requests → New pull request → use the "base" dropdown to pick the target branch (e.g., `main`) and the "compare" dropdown to pick your branch (e.g., `BRANCH`) → click "Create pull request" → provide a title and description → click "Create pull request".
3. To merge: open the PR page and click the green "Merge pull request" button. Confirm the merge type ("Create a merge commit" is default). After merging, the workflow YAML in the merged commit becomes part of the default branch and Actions will run automatically on subsequent triggers.

7) Helpful commands used during debugging

- Check git branch and remotes:
  git status --porcelain=2 --branch
  git remote -v
  git remote show origin
  git ls-remote --heads origin

- Create an SSH key and add to agent:
  ssh-keygen -t ed25519 -C "your_email@example.com"
  eval "$(ssh-agent -s)"
  ssh-add ~/.ssh/id_ed25519
  cat ~/.ssh/id_ed25519.pub

- Create a `main` branch and open a PR (if desired)
  git checkout -b main
  git push -u origin main

8) Maintenance tips

- Keep `requirements.txt` up to date so CI installs pinned deps.
- Add dependency caching for faster CI runs (we cache pip here).
- Add a linter step (flake8) and formatters to keep code clean.


If you want this file expanded into a more formal README or a checklist with links/screenshots, tell me what level of detail to add.
