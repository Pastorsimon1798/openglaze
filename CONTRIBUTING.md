# Contributing to OpenGlaze

Thank you for your interest in contributing to OpenGlaze! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a branch for your changes
4. Make your changes and test them
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional, for full stack)
- Node.js 20+ (for frontend tooling)

### Quick Start

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/openglaze.git
cd openglaze

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
python seed_data.py

# Run tests
pytest tests/

# Start development server
python server.py
```

Visit http://localhost:8768 to see the application.

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-batch-calculator` — New features
- `bugfix/fix-umf-calculation` — Bug fixes
- `docs/update-installation-guide` — Documentation updates
- `refactor/simplify-chemistry-engine` — Code refactoring

### Areas of Contribution

We welcome contributions in these areas:

- **Chemistry Engine** — UMF calculations, compatibility analysis, thermal expansion
- **AI Features** — Kama assistant improvements, prompt engineering, context retrieval
- **Frontend** — UI/UX improvements, accessibility, mobile responsiveness
- **Documentation** — Guides, tutorials, API docs
- **Testing** — Unit tests, integration tests, end-to-end tests
- **Performance** — Database optimization, caching, query improvements
- **DevOps** — Docker improvements, CI/CD, deployment scripts
- **Ceramic Data** — New recipes, materials, firing schedules, studio templates

## Testing

All contributions should include appropriate tests:

```bash
# Run the full test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_chemistry.py -v
```

### Test Guidelines

- Write tests for new features
- Update tests when modifying existing behavior
- Aim for >80% code coverage for new code
- Use descriptive test names that explain what is being tested

## Pull Request Process

1. **Update documentation** if your changes affect user-facing behavior
2. **Add tests** for new functionality
3. **Ensure all tests pass** before submitting
4. **Fill out the PR template** with a clear description of changes
5. **Link related issues** using `Fixes #123` or `Closes #456`
6. **Request review** from maintainers

### PR Review Criteria

- Code follows the project's style (PEP 8 for Python)
- Tests pass and coverage is maintained
- Documentation is updated
- Changes are focused and atomic
- Commit messages are clear and descriptive

## Commit Message Guidelines

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:

- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation changes
- `style` — Formatting, no code change
- `refactor` — Code refactoring
- `test` — Adding or updating tests
- `chore` — Build process, dependencies
- `perf` — Performance improvements
- `ci` — CI/CD changes

Examples:

```
feat(chemistry): add thermal expansion coefficient calculation

fix(ai): resolve Kama context injection for large glaze libraries

docs(readme): update self-hosting instructions for Docker
test(auth): add Kratos session validation tests
```

## Documentation

- Update `README.md` if you change project-wide behavior
- Update files in `docs/` for detailed guides
- Add inline documentation for complex functions
- Update `CHANGELOG.md` with your changes

## Community

- **GitHub Discussions** — For questions, ideas, and general discussion
- **GitHub Issues** — For bug reports and feature requests
- **Pull Requests** — For code contributions

## License

By contributing to OpenGlaze, you agree that your contributions will be licensed under the [MIT License](LICENSE).
