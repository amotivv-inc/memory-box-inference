# Contributing to OpenAI Inference Proxy

Thank you for your interest in contributing! We welcome contributions from the community.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/openai-inference-proxy.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Push to your fork: `git push origin feature/your-feature-name`
6. Create a Pull Request

## Development Setup

```bash
# Clone and enter the directory
git clone https://github.com/yourusername/openai-inference-proxy.git
cd openai-inference-proxy

# Run the quickstart script
./scripts/quickstart.sh

# Or set up manually
cp .env.example .env
# Add your keys to .env
docker-compose -f docker/docker-compose.yml up -d
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Keep functions focused and small
- Add docstrings to all public functions
- Format code with `black` and sort imports with `isort`

## Testing

Run the test suite before submitting:

```bash
./tests/test_all_endpoints.sh
```

## Pull Request Guidelines

1. **Keep PRs focused** - One feature or fix per PR
2. **Update tests** - Add tests for new functionality
3. **Update docs** - Keep documentation in sync with code changes
4. **Follow existing patterns** - Maintain consistency with the codebase
5. **Write clear commit messages** - Explain what and why

## Commit Messages

Use clear, descriptive commit messages:
- `feat: Add user-scoped API key validation`
- `fix: Correct streaming response handling`
- `docs: Update deployment guide`
- `test: Add tests for rating endpoint`

## Reporting Issues

When reporting issues, please include:
- Python version
- Docker version
- Steps to reproduce
- Expected vs actual behavior
- Any error messages

## Questions?

Feel free to open an issue for questions or discussions about potential changes.
