# steamstudy

The Steam Success Study pipeline (Collect, Build) and the offline Tag Network app. The full operating instructions are in [docs/running-guide.md](docs/running-guide.md).

**Researchers who only want to explore the results** do not need this repository or uv: ask for an **App Bundle** (one zip with the app, the Builds and the [User Guide](docs/user-guide/README.md)), extract it and double-click the launcher; it needs only Python 3.12–3.14. See [Getting started](docs/user-guide/01-getting-started.md#open-the-app). Making a bundle is described in the Running Guide, [Making an App Bundle](docs/running-guide.md#making-an-app-bundle).

## Install (running the pipeline)

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
