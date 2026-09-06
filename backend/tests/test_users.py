from app.api.v1.users import get_my_stats
from app.models import ChildProfile


async def test_get_my_stats_returns_profile_status() -> None:
    profile = ChildProfile(
        profile_id=1,
        parent_id=1,
        nickname="별이",
        age=7,
        password_hash="hash",
        streak_days=4,
        hearts=120,
        energy=3,
        max_energy=5,
    )

    response = await get_my_stats(current_profile=profile)

    assert response == {
        "success": True,
        "data": {
            "streak": 4,
            "hearts": 120,
            "xpPercent": 0.6,
        },
    }
