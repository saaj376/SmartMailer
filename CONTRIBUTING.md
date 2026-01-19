# Contributing to SmartMailer

Thank you for considering contributing to SmartMailer! We appreciate your interest in improving this project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with the following information:
- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, etc.)
- Any relevant logs or error messages

### Suggesting Enhancements

We welcome suggestions for new features or improvements! Please create an issue with:
- A clear and descriptive title
- A detailed description of the proposed enhancement
- Any relevant examples or use cases
- Why this enhancement would be useful

### Pull Requests

1. **Fork the repository** and create your branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Set up your development environment**:
   ```bash
   # Clone your fork
   git clone https://github.com/your-username/SmartMailer.git
   cd SmartMailer
   
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install pytest pytest-cov  # For testing
   ```

3. **Make your changes**:
   - Write clear, readable code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Run tests** to ensure everything works:
   ```bash
   pytest
   ```

5. **Commit your changes**:
   - Write clear, concise commit messages
   - Reference any related issues (e.g., "Fixes #123")
   ```bash
   git commit -m "Add feature: description of your changes"
   ```

6. **Push to your fork** and submit a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style Guidelines

- Follow [PEP 8](https://pep8.org/) style guide for Python code
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Keep functions focused and concise
- Add type hints where appropriate

### Testing

- Write unit tests for new functionality
- Ensure all tests pass before submitting a PR
- Aim for high test coverage
- Test with Python 3.9+ to ensure compatibility

### Documentation

- Update the README.md if you change functionality
- Update DOCS.md for user-facing changes
- Add docstrings to new functions and classes
- Include code examples where helpful

## Code of Conduct

Please note that this project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Questions?

If you have questions about contributing, feel free to:
- Open an issue with the `question` label
- Reach out to the maintainers

## License

By contributing to SmartMailer, you agree that your contributions will be licensed under the MIT License.

## Recognition

All contributors will be recognized in the project. Thank you for helping make SmartMailer better!
