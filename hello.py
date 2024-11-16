from datetime import datetime

from atproto import Client
from pydantic_settings import BaseSettings, SettingsConfigDict
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer
from textual.widgets import Footer, Header, Static
from zoneinfo import ZoneInfo


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bsky_handle: str
    bsky_password: str


def format_timestamp(timestamp: str) -> str:
    """Convert ISO timestamp to human readable format."""
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    local_dt = dt.astimezone(ZoneInfo("America/Chicago"))
    return local_dt.strftime("%b %d, %I:%M %p")


class PostWidget(Static):
    """A widget to display a single post."""

    def __init__(self, post_data, my_handle: str) -> None:
        super().__init__()
        self.post_data = post_data
        self.my_handle = my_handle

    def compose(self) -> ComposeResult:
        post = self.post_data.post
        author = post.author.display_name or post.author.handle
        is_my_post = post.author.handle == self.my_handle

        # Check if this is a reply
        is_reply = False
        reply_to = None
        if hasattr(post.record, "reply"):
            reply = post.record.reply
            if reply and reply.parent:
                is_reply = True
                # We only have the URI of the parent post, not the full content
                parent_uri = reply.parent.uri
                # Extract the handle from the URI (format: at://did:plc:handle/...)
                try:
                    reply_to = parent_uri.split("/")[2].split(":")[-1]
                except IndexError:
                    reply_to = "someone"

        # Format the post content
        created_at = format_timestamp(post.record.created_at)
        text = post.record.text
        likes = post.like_count or 0
        reposts = post.repost_count or 0

        # Build the header
        if reply_to:
            header = f"[b]{created_at}[/b]\n↩️ replying to [i]{reply_to}[/i]\n[b]@{author}[/b]"
        else:
            header = f"[b]{created_at}[/b]\n[b]@{author}[/b]"

        content = f"""{header}
{text}

❤️ {likes} | 🔄 {reposts}
───────────────"""

        # Set appropriate classes
        classes = ["my-post" if is_my_post else "other-post"]
        if is_reply:
            classes.append("reply")

        yield Static(content, classes=" ".join(classes))


class BlueskyApp(App):
    """A Textual app to display Bluesky posts."""

    CSS_PATH = "hello.tcss"
    TITLE = "Bluesky Posts"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(ScrollableContainer(id="posts_container"), id="main")
        yield Footer()

    def on_mount(self) -> None:
        self.load_posts()

    def action_refresh(self) -> None:
        posts_container = self.query_one("#posts_container")
        posts_container.remove_children()
        self.load_posts()

    def load_posts(self) -> None:
        settings = Settings()
        client = Client()
        profile = client.login(settings.bsky_handle, settings.bsky_password)

        posts = client.app.bsky.feed.get_author_feed({"actor": profile.did})
        posts_container = self.query_one("#posts_container")

        for post in posts.feed:
            posts_container.mount(PostWidget(post, settings.bsky_handle))


if __name__ == "__main__":
    app = BlueskyApp()
    app.run()
