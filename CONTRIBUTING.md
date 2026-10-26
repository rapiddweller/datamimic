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

One check applies to everybody: `make architecture-check`. Run it before you open a pull request.

The check fails when one of these is true:

- The code has an architecture violation, or the baseline in `known-violations.json` drifts.
- A measurement budget is exceeded, or the report is incomplete.
- The set of UNKNOWN findings differs from the set the review record assesses.
- A budget or a baseline entry in `known-violations.json` differs from the one the review record names.

A code change that does none of this, and changes neither the architecture contract nor the analyzer, needs no review record. Do not edit `docs/architecture/refactoring-study/experiment-2/completion-unknowns.json`.

A maintainer records a review only when the set of UNKNOWN findings, the validation diagnostics, the contract, the analyzer, or `known-violations.json` changes. If your change causes that, the maintainer adds the record to your branch.

A budget or baseline change in `known-violations.json` needs a `measurement_amendment` entry and the new `known_violations_digest` in the same pull request. A maintainer can still raise a ratchet budget when the raise is argued and verified.

The independent architecture review stays a required process step. It is recorded as a review note under `docs/architecture/refactoring-study/experiment-2/`, or as an approving review on the pull request, not as a digest.

---

## 💬 Community

Join our [GitHub Discussions](https://github.com/rapiddweller/datamimic/discussions) to share ideas, ask questions, or discuss potential features and improvements.

---

## 🙌 Recognition

We deeply appreciate your effort! Contributors will be recognized in our release notes and contributor lists.

Thank you for helping make DATAMIMIC even better! 🚀💖
