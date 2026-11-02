# Contributing to SciTeX

Thank you for your interest in contributing to SciTeX. This guide covers the
process for reporting issues, suggesting features, and submitting code.

## Contributor License Agreement

Before your first contribution can be merged, you must agree to the
[SciTeX CLA](CLA.md). This is a one-time process. The CLA ensures that:

- You retain copyright of your work.
- The project can continue to offer dual licensing (free for researchers,
  commercial for enterprises).

See [CLA.md](CLA.md) for full details.

## Reporting Issues

- Search [existing issues](https://github.com/scitex-ai/figrecipe/issues)
  before opening a new one.
- Include a minimal reproducible example when reporting bugs.
- Specify your Python version, OS, and `scitex` version.

## Development Setup

```bash
git clone git@github.com:scitex-ai/figrecipe.git
cd figrecipe
pip install -e ".[all,dev]"
```

## Branch Workflow

- `main` — stable releases only. Do not push directly.
- `develop` — integration branch. PRs target here.
- Feature branches — create from `develop`, name as `feature/<description>`.

```bash
git checkout develop
git checkout -b feature/my-change
# ... make changes ...
git push origin feature/my-change
# Open PR targeting develop
```

## Code Style

- Follow existing conventions in the codebase.
- Use `_` prefix for internal/private modules and functions.
- Keep files under 512 lines.
- Run tests before submitting:

```bash
pytest tests/ -x -q
```

## Pull Request Process

1. Ensure your branch is up to date with `develop`.
2. Write tests for new functionality.
3. Run the test suite and confirm all tests pass.
4. Open a PR targeting `develop` with a clear description.
5. The CLA bot will check your CLA status on your first PR.

## License

By contributing, you agree to the terms of the [CLA](CLA.md), which includes
licensing under AGPL-3.0 (see [LICENSE](LICENSE)) and the dual-licensing
provisions described therein.

## Frontend owner and builds

The editor requires public `scitex-sdk==0.3.17`. Its Python wheel carries the
frontend package exposed by `scitex_sdk.get_frontend_package_dir()`. For a local
frontend build with that installed owner:

```bash
cd src/figrecipe/_django/frontend
python configure.py
npm install
npm run test:header
npm run build
npm run build:lib
```

`configure.py` validates the SDK package identity and public React bridge, then
records its local absolute file dependency. Review these local package/lock
changes before committing: the tracked files retain the portable sibling SDK
layout used by the release workflow, rather than a contributor's install path.
The web build reads the repository's root `pyproject.toml` for its version;
copying only the frontend directory is insufficient. Both web and library
builds use the same SDK owner. Release CI checks out its immutable released
source recorded in the workflow and frontend metadata.
