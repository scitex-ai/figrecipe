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

- Search [existing issues](https://github.com/ywatanabe1989/figrecipe/issues)
  before opening a new one.
- Include a minimal reproducible example when reporting bugs.
- Specify your Python version, OS, and `scitex` version.

## Development Setup

```bash
git clone git@github.com:ywatanabe1989/figrecipe.git
cd figrecipe
pip install -e ".[dev]"
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

## Local Audit Caveats

Running `scitex-dev ecosystem audit-all figrecipe` locally can produce a
**misleadingly large violation count** compared to CI. This happens because
editable installs (`pip install -e .`) leave an incomplete/empty RECORD file
in the package's `.dist-info` directory. Local audit tooling misreads the
missing RECORD and flags every file as a violation.

CI uses a full non-editable wheel install with a complete RECORD, so the
same rules pass cleanly there. Treat inflated local counts with skepticism
— check whether violations cluster around RECORD-related rules. For a
definitive result, run the audit from CI or on a non-editable install.

## License

By contributing, you agree to the terms of the [CLA](CLA.md), which includes
licensing under AGPL-3.0 (see [LICENSE](LICENSE)) and the dual-licensing
provisions described therein.
