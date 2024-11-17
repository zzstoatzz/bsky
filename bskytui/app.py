from collections import defaultdict

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer
from textual.widgets import Button, Footer, Header, Static

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
        self.current_cursor = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(id="stats"),
            ScrollableContainer(id="posts_container", can_focus=True),
            id="main",
        )
        yield Footer()

    async def on_mount(self) -> None:
        self.update_stats()
        await self.load_posts(initial=True)

    async def load_posts(self, initial: bool = False) -> None:
        """Load posts and update UI."""
        posts_container = self.query_one("#posts_container")

        # Remove old load more button
        for old_button in posts_container.query("#load_more"):
            await old_button.remove()

        # Only clear container on initial load
        if initial:
            posts_container.remove_children()
            self.current_cursor = None

        # Get new posts
        if self.current_view == "timeline":
            posts, next_cursor = self.service.get_timeline(self.current_cursor)
        else:
            posts, next_cursor = self.service.get_author_feed(self.current_cursor)

        if not posts:
            return

        self.current_cursor = next_cursor

        # Group and mount new posts
        post_map = {}
        reply_map = defaultdict(list)

        for post in posts:
            post_map[post.post.uri] = post
            if hasattr(post.post.record, "reply") and post.post.record.reply:
                parent_uri = post.post.record.reply.parent.uri
                reply_map[parent_uri].append(post)

        for post in posts:
            if not (hasattr(post.post.record, "reply") and post.post.record.reply):
                posts_container.mount(PostWidget(post, self.service.profile.handle))
                for reply in reply_map.get(post.post.uri, []):
                    posts_container.mount(
                        PostWidget(reply, self.service.profile.handle)
                    )

        # Add load more button if there are more posts
        if next_cursor:
            load_button = Button("Load More Posts", id="load_more", variant="primary")
            posts_container.mount(load_button)

        # Only scroll to top on initial load
        if initial:
            posts_container.scroll_home()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "load_more":
            await self.load_posts()

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

    async def action_show_timeline(self) -> None:
        self.current_view = "timeline"
        self.update_stats()
        await self.refresh_posts()

    async def action_show_my_posts(self) -> None:
        self.current_view = "my_posts"
        self.update_stats()
        await self.refresh_posts()

    async def action_refresh(self) -> None:
        await self.refresh_posts()

    async def refresh_posts(self) -> None:
        posts_container = self.query_one("#posts_container")
        posts_container.remove_children()
        await self.load_posts()

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
