# Contributing to Lodestar

Thank you for your interest in contributing to Lodestar!

## How to Contribute

### Reporting Issues

- Use GitHub Issues
- Provide clear reproduction steps
- Include system information (OS, Python version, etc.)
- Share relevant log files

### Suggesting Features

- Open a GitHub Discussion first
- Describe the problem you're trying to solve
- Explain why existing features don't address it
- Be open to alternative solutions

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test thoroughly
5. Document in relevant .md files
6. Create ADR if it's an architectural change
7. Submit PR with clear description

## Development Setup
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ProjectLodestar.git
cd ProjectLodestar

# Create a feature branch
git checkout -b feature/your-feature

# Make changes and test
./scripts/status.sh
./scripts/quick-start.sh

# Commit with clear messages
git commit -m "feat: add new routing strategy"
```

## Code Style

### Shell Scripts
- Use `#!/bin/bash` shebang
- Include descriptive comments
- Error handling with clear messages
- Use `set -e` for critical scripts

### Python
- Follow PEP 8
- Use type hints where possible
- Document functions with docstrings

### Documentation
- Use Markdown
- Include code examples
- Keep explanations concise
- Update TOC if adding sections

## Testing

Test your changes:
1. Clean install on fresh VM (if possible)
2. Run through SETUP.md steps
3. Test with real coding projects
4. Verify all scripts work
5. Check documentation accuracy

## Commit Messages

Format: `type: description`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
- `feat: add automatic model selection based on prompt`
- `fix: router fails to start on port conflict`
- `docs: update ARCHITECTURE.md with new components`

## Architecture Decisions

For significant changes:
1. Create ADR: `./scripts/adr-new.sh "Your Decision"`
2. Fill out all sections
3. Discuss in PR
4. Mark as Accepted when merged

## License

By contributing, you agree your contributions will be licensed under the MIT License.

## Questions?

Open a GitHub Discussion or reach out in Issues.

Thank you for making Lodestar better! 🌟
