"""Unit tests for GeniusHub resource management."""

import unittest
from unittest.mock import AsyncMock, patch
from geniushubclient import GeniusHub


class TestResourceManagement(unittest.IsolatedAsyncioTestCase):
    """Test case for GeniusHub resource management."""

    async def test_close_closes_session(self):
        """Verify that GeniusHub.close() closes the underlying aiohttp session."""
        mock_session = AsyncMock()
        hub = GeniusHub(hub_id="test_token", session=mock_session)

        # Verify session is the one we passed
        self.assertEqual(hub.genius_service._session, mock_session)

        # Act
        await hub.close()

        # Assert
        mock_session.close.assert_awaited_once()

    async def test_close_without_session(self):
        """Verify that GeniusHub.close() cleans up an internally created session."""
        mock_session = AsyncMock()
        with patch(
            "geniushubclient.session.aiohttp.ClientSession", return_value=mock_session
        ):
            hub = GeniusHub(hub_id="test_token")
            await hub.close()
        mock_session.close.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
