from collections import defaultdict
from datetime import datetime
from time import sleep
from typing import Dict

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
        self.bsky_link = f"https://bsky.app/profile/{post_data.post.author.handle}/post/{post_data.post.uri.split('/')[-1]}"

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
                try:
                    reply_to = reply.parent.uri.split("/")[2].split(":")[-1]
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

        content = f"""[dim]{header}[/dim]

[bold]{text}[/bold]

[dim]❤️ {likes} | 🔄 {reposts}
───────────────[/dim]"""

        # Set appropriate classes
        classes = ["my-post" if is_my_post else "other-post"]
        if is_reply:
            classes.append("reply")

        yield Static(content, classes=" ".join(classes))


class SocialStats(Static):
    """Widget to display follower/following counts and current view."""

    def __init__(self, followers: int, following: int, current_view: str) -> None:
        super().__init__()
        self.followers = followers
        self.following = following
        self.current_view = current_view.replace(
            "_", " "
        ).title()  # "timeline" -> "Timeline"

    def compose(self) -> ComposeResult:
        yield Static(
            f"[b]{self.current_view}[/b] | [b]Following:[/b] {self.following} | [b]Followers:[/b] {self.followers}"
        )


class BlueskyApp(App):
    """A Textual app to display Bluesky posts."""

    CSS_PATH = "bskytui.tcss"
    TITLE = "Bluesky Posts"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("1", "show_timeline", "Timeline", show=True),
        Binding("2", "show_my_posts", "My Posts", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.client: Client | None = None
        self.profile = None
        self.following: Dict = {}
        self.current_view = "timeline"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(id="stats"), ScrollableContainer(id="posts_container"), id="main"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.setup_client()
        self.load_social_data()
        self.load_posts()

    def setup_client(self) -> None:
        settings = Settings()
        self.client = Client()
        self.profile = self.client.login(settings.bsky_handle, settings.bsky_password)

    def update_stats(self) -> None:
        """Update the stats widget with current information."""
        profile_response = self.client.app.bsky.actor.get_profile(
            {"actor": self.profile.handle}
        )

        stats_widget = self.query_one("#stats")
        stats_widget.remove_children()
        stats_widget.mount(
            SocialStats(
                followers=profile_response.followers_count,
                following=profile_response.follows_count,
                current_view=self.current_view,
            )
        )

    def load_social_data(self) -> None:
        """Load following and follower data."""
        self.update_stats()

        # We can still fetch the follows/followers lists if needed for other features
        self.following = self._get_follows()
        self.followers = self._get_followers()

    def _get_follows(self, limit: int = 100) -> Dict:
        """Get accounts the user follows."""
        follows = defaultdict(str)
        cursor = None

        while True:
            response = self.client.get_follows(
                actor=self.profile.handle,
                cursor=cursor,
                limit=min(100, limit - len(follows)),
            )

            for follow in response.follows:
                follows[follow.did] = {
                    "handle": follow.handle,
                    "created_at": follow.created_at,
                }

            if len(follows) >= limit or not response.cursor:
                break

            cursor = response.cursor
            sleep(0.5)

        return follows

    def _get_followers(self, limit: int = 100) -> Dict:
        """Get accounts following the user."""
        followers = defaultdict(str)
        cursor = None

        while True:
            response = self.client.get_followers(
                actor=self.profile.handle,
                cursor=cursor,
                limit=min(100, limit - len(followers)),
            )

            for follower in response.followers:
                followers[follower.did] = {
                    "handle": follower.handle,
                    "created_at": follower.created_at,
                }

            if len(followers) >= limit or not response.cursor:
                break

            cursor = response.cursor
            sleep(0.5)

        return followers

    def action_show_timeline(self) -> None:
        """Show the main timeline feed."""
        self.current_view = "timeline"
        self.update_stats()
        self.refresh_posts()

    def action_show_my_posts(self) -> None:
        self.current_view = "my_posts"
        self.update_stats()
        self.refresh_posts()

    def action_refresh(self) -> None:
        self.refresh_posts()

    def refresh_posts(self) -> None:
        posts_container = self.query_one("#posts_container")
        posts_container.remove_children()
        self.load_posts()

    def load_posts(self) -> None:
        posts_container = self.query_one("#posts_container")

        if self.current_view == "timeline":
            # Get the main timeline feed
            posts = self.client.app.bsky.feed.get_timeline()
        else:  # my_posts view
            posts = self.client.app.bsky.feed.get_author_feed(
                {"actor": self.profile.did}
            )

        for post in posts.feed:
            posts_container.mount(PostWidget(post, self.profile.handle))


if __name__ == "__main__":
    app = BlueskyApp()
    app.run()
