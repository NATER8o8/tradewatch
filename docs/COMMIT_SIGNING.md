Commit Signing (SSH)
--------------------

This repository prefers signed commits. The project supports SSH-based commit signing (OpenSSH key format).

Quick steps (what we did for you):

- Generated an ed25519 key at `~/.ssh/id_ed25519` (protected by a passphrase).
- Added the public key to your GitHub account (Settings → SSH and GPG keys).
- Configured Git to use SSH signing:
  - `git config --global gpg.format ssh`
  - `git config --global user.signingkey ~/.ssh/id_ed25519.pub`
  - `git config --global commit.gpgsign true`

Verify a signed commit locally:

1. Ensure the key is loaded into an agent:

   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```

2. (Optional) Create an allowed-signers file for local verification:

   ```bash
   # repo-local example
   mkdir -p .git/trust
   cp ~/.ssh/id_ed25519.pub .git/trust/allowed_signers
   git config gpg.ssh.allowedSignersFile .git/trust/allowed_signers
   ```

3. Create a signed commit and check it:

   ```bash
   git commit --allow-empty -m "chore: test signed commit"
   git log -1 --show-signature
   ```

GitHub verification
-------------------

After pushing signed commits to GitHub, the web UI will show "Verified" for commits signed by keys in your account. Local verification (via `git log --show-signature`) requires the allowed-signers file configuration shown above.

Notes
-----
- If you prefer GPG signing (OpenPGP), see `gpg --full-generate-key` and set `git config --global gpg.program gpg`.
- For contributor docs, consider adding a short paragraph to `CONTRIBUTING.md` linking to this file.
