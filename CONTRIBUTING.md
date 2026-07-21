# Contributing

Small, focused pull requests are easiest to review.

1. Create a branch from the latest `main`.
2. Keep code compatible with Python 3.10 and the standard library.
3. Run the full unit suite and `compileall`.
4. Update tests for behavior changes.
5. Explain which host integrations were actually exercised.

For catalog changes, follow [DATA.md](DATA.md): cite a reliable edition or
bibliographic source, keep unrelated wording untouched, and refresh documented
counts when records are added or removed.

Do not enable ambient mode during tests against a contributor's real home
directory. Patch the config functions or set `HOME` to an isolated temporary
directory.
