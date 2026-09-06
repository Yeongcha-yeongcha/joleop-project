from datetime import UTC, datetime

from app.core.config import settings
from app.models import ChildProfile


class RewardService:
    def apply_completion_reward(self, profile: ChildProfile) -> dict:
        hearts = settings.COMPLETION_REWARD_HEARTS
        energy = settings.COMPLETION_REWARD_ENERGY
        profile.hearts = (profile.hearts or 0) + hearts
        profile.energy = min((profile.energy or 0) + energy, profile.max_energy or 5)
        if profile.energy >= (profile.max_energy or 5):
            profile.energy_recharged_at = datetime.now(UTC)
        return {"hearts": hearts, "energy": energy}
