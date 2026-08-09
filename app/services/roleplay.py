from app.models import RoleplayMission


class RoleplayService:
    async def respond(
        self,
        *,
        mission: RoleplayMission,
        transcript: str,
        turn: int,
    ) -> dict:
        raise NotImplementedError


class MockRoleplayService(RoleplayService):
    async def respond(
        self,
        *,
        mission: RoleplayMission,
        transcript: str,
        turn: int,
    ) -> dict:
        return {
            "speaker": mission.character_name.upper(),
            "text": "Thank you! I knew it!",
            "score": 90,
        }
