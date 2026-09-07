from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.exceptions import InsufficientEnergyException
from app.models import ChildProfile


class EnergyService:
    def consume_for_learning(self, profile: ChildProfile, *, now: datetime | None = None) -> dict:
        now = now or datetime.now(UTC)
        energy = self.apply_recharge(profile, now=now)
        current_energy = energy["energy"]
        if current_energy <= 0:
            raise InsufficientEnergyException()

        profile.energy = current_energy - 1
        max_energy = profile.max_energy or 5
        profile.energy_recharged_at = now

        next_seconds = 0 if profile.energy >= max_energy else settings.ENERGY_RECHARGE_MINUTES * 60
        return {
            "energy": profile.energy,
            "maxEnergy": max_energy,
            "energyRechargeMinutes": settings.ENERGY_RECHARGE_MINUTES,
            "nextEnergyInSeconds": next_seconds,
        }

    def apply_recharge(self, profile: ChildProfile, *, now: datetime | None = None) -> dict:
        now = now or datetime.now(UTC)
        max_energy = profile.max_energy or 5
        current_energy = min(profile.energy or 0, max_energy)
        interval_seconds = settings.ENERGY_RECHARGE_MINUTES * 60
        anchor = profile.energy_recharged_at or now

        if current_energy >= max_energy:
            profile.energy = max_energy
            profile.energy_recharged_at = now
            return {
                "energy": max_energy,
                "maxEnergy": max_energy,
                "energyRechargeMinutes": settings.ENERGY_RECHARGE_MINUTES,
                "nextEnergyInSeconds": 0,
            }

        elapsed = max(0, int((now - anchor).total_seconds()))
        gained = elapsed // interval_seconds
        if gained > 0:
            current_energy = min(max_energy, current_energy + gained)
            profile.energy = current_energy
            profile.energy_recharged_at = now if current_energy >= max_energy else anchor + timedelta(seconds=gained * interval_seconds)

        if current_energy >= max_energy:
            next_seconds = 0
        else:
            elapsed_after_anchor = max(0, int((now - profile.energy_recharged_at).total_seconds()))
            next_seconds = interval_seconds - (elapsed_after_anchor % interval_seconds)

        return {
            "energy": current_energy,
            "maxEnergy": max_energy,
            "energyRechargeMinutes": settings.ENERGY_RECHARGE_MINUTES,
            "nextEnergyInSeconds": next_seconds,
        }
