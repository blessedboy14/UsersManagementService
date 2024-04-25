import pytest

from src.auth.service import get_by_email


@pytest.mark.asyncio
async def test_get_user_by_email(mocker):
    mock_session = mocker.AsyncMock()

    mocker.patch('src.database.database.get_session', return_value=mock_session)

    mock_query = mocker.Mock()
    mock_query.first.return_value = {"email": "<EMAIL>", "username": "test", "phone": "+375291234567"}
    mock_session.query.return_value = mock_query

    user = await get_by_email("<EMAIL>", mock_session)

    assert user == {"email": "<EMAIL>", "username": "test", "phone": "+375291234567"}

