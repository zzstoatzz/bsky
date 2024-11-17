from textual.app import ComposeResult
from textual.widgets import Button, Static

from bskytui.utils.formatters import format_timestamp


class PostWidget(Static):
    """A widget to display a single post."""

    def __init__(self, post_data, my_handle: str) -> None:
        super().__init__()
        self.post_data = post_data
        self.my_handle = my_handle
        self.post_rkey = post_data.post.uri.split("/")[-1]
        self.bsky_link = f"https://bsky.app/profile/{post_data.post.author.handle}/post/{self.post_rkey}"

    def compose(self) -> ComposeResult:
        post = self.post_data.post
        author = post.author.display_name or post.author.handle
        is_my_post = post.author.handle == self.my_handle

        # Format content
        created_at = format_timestamp(post.record.created_at)
        text = post.record.text
        likes = post.like_count or 0
        reposts = post.repost_count or 0

        # Build the header
        header = self._build_header(post, author, created_at)
        content = self._build_content(header, text, likes, reposts)

        # Set appropriate classes
        classes = []
        if is_my_post:
            classes.append("my-post")
        else:
            classes.append("other-post")
        if self._is_reply(post):
            classes.append("reply")

        yield Static(content, classes=" ".join(classes))
        if is_my_post:
            yield Button("🗑️", id=f"delete-{self.post_rkey}", classes="delete-btn")

    def _build_header(self, post, author, created_at) -> str:
        reply_info = self._get_reply_info(post)
        if reply_info:
            return f"[b]{created_at}[/b]\n↩️ {reply_info}"
        return f"[b]{created_at}[/b]\n[b]@{author}[/b]"

    def _get_reply_info(self, post) -> str | None:
        """Get formatted reply information."""
        if not self._is_reply(post):
            return None

        try:
            parent = post.record.reply.parent
            parent_did = parent.uri.split("/")[2]

            parent_handle = self.app.service.get_profile_by_did(parent_did)
            current_handle = post.author.handle

            if parent_handle == current_handle:
                return f"[i]@{current_handle} replied to themselves[/i]"

            return f"[i]@{current_handle} replied to @{parent_handle}[/i]"

        except (IndexError, AttributeError):
            return f"[i]@{post.author.handle} replied to someone[/i]"

    def _build_content(self, header: str, text: str, likes: int, reposts: int) -> str:
        return f"""[dim]{header}[/dim]
[bold]{text}[/bold]
[dim]❤️ {likes} | 🔄 {reposts}[/dim]"""

    def _is_reply(self, post) -> bool:
        return (
            hasattr(post.record, "reply")
            and post.record.reply
            and post.record.reply.parent
        )

    def _get_reply_to(self, post) -> str | None:
        if not self._is_reply(post):
            return None
        try:
            return post.record.reply.parent.uri.split("/")[2].split(":")[-1]
        except IndexError:
            return "someone"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id.startswith("delete-"):
            post_rkey = event.button.id.replace("delete-", "")
            self.app.delete_post(post_rkey, self)
