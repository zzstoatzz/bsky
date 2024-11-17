from textual.app import ComposeResult
from textual.widgets import Static

from bskytui.utils.formatters import format_timestamp


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

        # Format content
        created_at = format_timestamp(post.record.created_at)
        text = post.record.text
        likes = post.like_count or 0
        reposts = post.repost_count or 0

        # Build the header
        header = self._build_header(post, author, created_at)
        content = self._build_content(header, text, likes, reposts)

        # Set appropriate classes
        classes = ["my-post" if is_my_post else "other-post"]
        if self._is_reply(post):
            classes.append("reply")

        yield Static(content, classes=" ".join(classes))

    def _build_header(self, post, author: str, created_at: str) -> str:
        reply_to = self._get_reply_to(post)
        if reply_to:
            return f"[b]{created_at}[/b]\n↩️ replying to [i]{reply_to}[/i]\n[b]@{author}[/b]"
        return f"[b]{created_at}[/b]\n[b]@{author}[/b]"

    def _build_content(self, header: str, text: str, likes: int, reposts: int) -> str:
        return f"""[dim]{header}[/dim]

[bold]{text}[/bold]

[dim]❤️ {likes} | 🔄 {reposts}
───────────────[/dim]"""

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
