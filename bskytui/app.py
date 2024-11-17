from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer
from textual.widgets import Footer, Header, Static

from bskytui.services.bsky import BlueskyService
from bskytui.widgets.post import PostWidget
from bskytui.widgets.stats import SocialStats


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
        self.service = BlueskyService()
        self.current_view = "timeline"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(id="stats"), ScrollableContainer(id="posts_container"), id="main"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.update_stats()
        self.load_posts()

    def update_stats(self) -> None:
        """Update the stats widget with current information."""
        stats = self.service.get_profile_stats()

        stats_widget = self.query_one("#stats")
        stats_widget.remove_children()
        stats_widget.mount(
            SocialStats(
                followers=stats["followers_count"],
                following=stats["follows_count"],
                current_view=self.current_view,
            )
        )

    def action_show_timeline(self) -> None:
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

        posts = (
            self.service.get_timeline()
            if self.current_view == "timeline"
            else self.service.get_author_feed()
        )

        for post in posts:
            posts_container.mount(PostWidget(post, self.service.profile.handle))


if __name__ == "__main__":
    app = BlueskyApp()
    app.run()
