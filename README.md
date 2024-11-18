# demo bsky tui

> [!NOTE]
> This project is under development and requires using python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/) (you should use uv anyways 🙂)

set the following environment variables (export or `.env` file):
```
export BSKY_HANDLE=your_handle.bsky.social
export BSKY_PASSWORD=your_password
```

## Run directly (no installation needed)
```bash
uvx bskytui
```

## Or clone and run locally
```bash
git clone https://github.com/zzstoatzz/bsky
cd bsky
uv sync
uv run bskytui/app.py
```