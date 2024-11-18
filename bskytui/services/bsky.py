from collections import defaultdict
from time import sleep

from atproto import Client

from bskytui.config.settings import Settings


class BlueskyService:
    def __init__(self):
        self.client = None
        self.profile = None
        self._setup_client()

    def _setup_client(self) -> None:
        settings = Settings()
        self.client = Client()
        self.profile = self.client.login(settings.bsky_handle, settings.bsky_password)

    def get_timeline(self, cursor: str | None = None) -> tuple[list, str | None]:
        """Get main timeline feed.

        Returns:
            Tuple of (posts, cursor)
        """
        response = self.client.app.bsky.feed.get_timeline({'cursor': cursor})
        return response.feed, response.cursor

    def get_author_feed(self, cursor: str | None = None) -> tuple[list, str | None]:
        """Get authenticated user's posts.

        Returns:
            Tuple of (posts, cursor)
        """
        response = self.client.app.bsky.feed.get_author_feed({'actor': self.profile.did, 'cursor': cursor})
        return response.feed, response.cursor

    def get_profile_stats(self) -> dict:
        """Get user profile statistics."""
        profile = self.client.app.bsky.actor.get_profile({'actor': self.profile.handle})
        return {
            'followers_count': profile.followers_count,
            'follows_count': profile.follows_count,
        }

    def get_follows(self, limit: int = 100) -> dict:
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
                    'handle': follow.handle,
                    'created_at': follow.created_at,
                }

            if len(follows) >= limit or not response.cursor:
                break

            cursor = response.cursor
            sleep(0.5)

        return follows

    def delete_post(self, post_uri: str) -> bool:
        """Delete a post by its URI."""
        try:
            # Extract the rkey (post ID) from the URI
            rkey = post_uri.split('/')[-1]

            # The actual deletion call
            response = self.client.com.atproto.repo.delete_record(
                {'repo': self.profile.did, 'collection': 'app.bsky.feed.post', 'rkey': rkey}
            )
            return True

        except Exception as e:
            print(f'Failed to delete post: {e}')  # Keep basic error logging
            return False

    def get_profile_by_did(self, did: str) -> str:
        """Get a user's handle from their DID."""
        try:
            profile = self.client.app.bsky.actor.get_profile({'actor': did})
            return profile.handle
        except Exception:
            return 'someone'
