## `bskytui`

> [!NOTE]
> This project is under development and requires using python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/) (you should use uv anyways 🙂)

set the following environment variables (export or `.env` file):
```
export BSKY_HANDLE=your_handle.bsky.social
export BSKY_PASSWORD=your_password
```

## Run directly (no installation needed)
```bash
uv bskytui
```

## Run in docker ()
```bash
docker run --rm -it --env-file .env ghcr.io/astral-sh/uv:python3.13-bookworm-slim uvx bskytui
```


## Install and run in a virtual environment
```bash
uv venv && source .venv/bin/activate
uv pip install bskytui
uv run bskytui
```

## Or clone (for development) and run
```bash
git clone https://github.com/zzstoatzz/bsky
cd bsky
uv run bskytui
```

## Development
```bash
# Install dev dependencies and run with hot reload
uv pip install -e ".[dev]"
uv run scripts/dev.py
```