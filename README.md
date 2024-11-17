# demo bsky tui

set the following environment variables (export or `.env` file):
```
export BSKY_HANDLE=your_handle.bsky.social
export BSKY_PASSWORD=your_password
```

then run (or the whole pip thing if you're not using uv):
```
git clone https://github.com/zzstoatzz/bsky
cd bsky
uv sync
uv run bskytui/app.py
```