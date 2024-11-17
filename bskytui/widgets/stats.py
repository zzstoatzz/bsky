from textual.app import ComposeResult
from textual.widgets import Static


class SocialStats(Static):
    """Widget to display follower/following counts and current view."""

    def __init__(self, followers: int, following: int, current_view: str) -> None:
        super().__init__()
        self.followers = followers
        self.following = following
        self.current_view = current_view.replace("_", " ").title()

    def compose(self) -> ComposeResult:
        yield Static(
            f"[b]{self.current_view}[/b] | [b]Following:[/b] {self.following} | [b]Followers:[/b] {self.followers}"
        )
