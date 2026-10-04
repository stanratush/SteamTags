# steamstudy

The Steam Success Study pipeline (Collect, Build) and the offline Tag Network app. The full operating instructions are in [docs/running-guide.md](docs/running-guide.md).

## Install

Requires [uv](https://docs.astral.sh/uv/) and Python 3.14.

```bash
uv sync --compile-bytecode
```

`pyproject.toml` also sets `compile-bytecode = true`, so a plain `uv sync` compiles bytecode too. Never set `PYTHONDONTWRITEBYTECODE`.

## Test

```bash
uv run python -W default -X faulthandler -m pytest
```

Never run the tests with `-X dev`: it crashes this machine's interpreters at exit.
