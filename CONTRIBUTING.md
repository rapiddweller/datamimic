# Contribution Guide 🌟

Thank you for your interest in contributing to **DATAMIMIC Community Edition**! Your contributions help us improve and evolve this platform, making it better for the entire community.

---

## 🌱 How to Contribute

### 1. 🚀 Getting Started

- **Fork the Repository**: Click on "Fork" to create your copy of DATAMIMIC.
- **Clone Your Fork**: Clone the forked repository to your local machine:

```bash
git clone https://github.com/your-username/datamimic.git
cd datamimic
```

### 2. 🛠️ Setup Your Development Environment

Ensure you have Python ≥3.11 installed. Then set up your environment:

```bash
pip install uv
uv sync
make install-pre-commit  # ruff format, ruff check and mypy run before each commit
```

### 3. 🌟 Make Your Changes

- Create a new branch for your feature or fix:

```bash
git checkout -b my-feature-or-fix
```

- Clearly comment and document your code.
- Follow existing coding styles and practices.

### 4. ✅ Submit a Pull Request

- Push your changes:

```bash
git push origin my-feature-or-fix
```

- Open a Pull Request (PR) on GitHub:
  - Clearly describe your changes.
  - Explain the rationale for your changes or fixes.
  - Link any related issues or feature requests.

---

## 🧑‍💻 Contribution Types

- **Bug Fixes**: Correct bugs and improve stability.
- **Features**: Add new functionalities or improvements.
- **Documentation**: Enhance or create clear documentation.
- **Tests**: Improve coverage and robustness with additional tests.

---

## 📜 Contribution Guidelines

- **Stay Relevant**: Ensure your contribution aligns with the DATAMIMIC roadmap.
- **Keep Quality High**: Maintain code quality, readability, and test coverage.
- **Discuss Major Changes**: Open an issue or discussion to propose significant changes before investing substantial effort.

---

## 🚦 CI

A code pull request runs ruff, mypy, the ArchKeel contract check, unit, integration and architecture tests, Windows portability proofs, and the Python 3.11 wheel smoke test. Documentation-only pull requests run documentation tests; documentation changes also trigger those tests on pushes. Non-PR code runs include coverage shards (including the nightly cases), functional and external-service tests, the determinism matrix, wheel smoke tests and Sonar. To start the main workflow for a branch before a risky merge, run `gh workflow run main.yml --ref <branch>`.

### Focused fast authoring tests

Test lanes are separated by physical paths. To run the fast pre-commit unit
lane during development:

```bash
uv run pytest tests_ce/unit_tests/precommit -n 2 -q
```

The main test paths are `tests_ce/unit_tests`, `tests_ce/integration_tests`,
`tests_ce/architecture`, and the functional and scenario suites. Longer tests
are in `tests_ce/nightly_tests`; scale tests in `tests_ce/manual_perf_tests`
run only by manual dispatch. Cross-process replay and its negative controls
remain part of the appropriate physical lane.

---

## 🏛️ Architecture Check

Run `make architecture-check` before opening a pull request. A cold install builds the pinned
ArchKeel Git commit with Rust and `cargo-auditable` (`cargo install --locked cargo-auditable@0.7.7`).
An ArchKeel rule verdict of FAIL fails CI. PASS and UNKNOWN are reported in the
[development architecture report](https://rapiddweller.github.io/datamimic/) with diagnostics.
Measurement changes and UNKNOWN findings do not require a baseline update or a review record.

Record the independent architecture review for changes to the contracts or under
`datamimic_ce/` as a review note or an approving review on the pull request.

---

## 💬 Community

Join our [GitHub Discussions](https://github.com/rapiddweller/datamimic/discussions) to share ideas, ask questions, or discuss potential features and improvements.

---

## 🙌 Recognition

We deeply appreciate your effort! Contributors will be recognized in our release notes and contributor lists.

Thank you for helping make DATAMIMIC even better! 🚀💖
