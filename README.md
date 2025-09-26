# Solver Controller

Service that handles the solvers to solve problem instances

## Usage 

Use `skaffold run -p prod` for production settings or `skaffold dev` for development settings.

## Contributing


Download the development dependencies by using `pip install -r requirements-dev.txt`.

### Updating dependencies
You can manually update dependencies by:
```bash
pip-compile pyproject.toml -o requirements.txt --strip-extras
pip-compile pyproject.toml --extra dev -o requirements-dev.txt --strip-extras
```
