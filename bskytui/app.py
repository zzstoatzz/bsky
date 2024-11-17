from collections import defaultdict

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

        # Group posts by parent
        post_map = {}  # uri -> post
        reply_map = defaultdict(list)  # parent_uri -> [child_posts]

        for post in posts:
            post_map[post.post.uri] = post
            if hasattr(post.post.record, "reply") and post.post.record.reply:
                parent_uri = post.post.record.reply.parent.uri
                reply_map[parent_uri].append(post)

        # Mount posts in order, with replies nested
        for post in posts:
            if not (hasattr(post.post.record, "reply") and post.post.record.reply):
                # This is a top-level post
                posts_container.mount(PostWidget(post, self.service.profile.handle))
                # Mount any replies to this post
                for reply in reply_map.get(post.post.uri, []):
                    posts_container.mount(
                        PostWidget(reply, self.service.profile.handle)
                    )

    def delete_post(self, post_uri: str, post_widget: PostWidget) -> None:
        """Delete a post and remove it from the UI if successful."""
        if self.service.delete_post(post_uri):
            post_widget.remove()
            self.notify("Post deleted successfully", severity="information")
        else:
            self.notify("Failed to delete post", severity="error")


if __name__ == "__main__":
    app = BlueskyApp()
    app.run()
