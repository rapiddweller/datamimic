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

## 🏛️ Architecture Check

The pull request check "ArchKeel architecture contract" runs `make architecture-check`.

### Outside contributors (pull requests from forks)

1. The check runs the substance part only.
2. It fails when the code adds a violation, exceeds a measurement budget, drifts from the baseline, or leaves the report incomplete.
3. It does not check the architecture review record. A maintainer owns that record.
4. A stale review record does not block your pull request.
5. Run `make architecture-check COMPLETION_GATE_FLAGS=--substance-only` to see the same result locally.

### Maintainers

Do these steps for each pull request for which the full check reports that the review record does not match:

1. Run `make architecture-check` on the branch. The run fails with "Validation changed after independent review." until the record is current.
2. Ask the independent reviewer to record the review in `docs/architecture/refactoring-study/experiment-2/completion-unknowns.json`.
3. Push the record to the contributor branch. Use the maintainer edit permission of the pull request.
4. Run `make architecture-check` again. It must pass.

Warning: a merge without the record turns `development` red, because pushes to `development` run the full check.

5. Merge the pull request.

### Same-repository branches

Branches in this repository run the full check, including the review record.

---

## 💬 Community

Join our [GitHub Discussions](https://github.com/rapiddweller/datamimic/discussions) to share ideas, ask questions, or discuss potential features and improvements.

---

## 🙌 Recognition

We deeply appreciate your effort! Contributors will be recognized in our release notes and contributor lists.

Thank you for helping make DATAMIMIC even better! 🚀💖
