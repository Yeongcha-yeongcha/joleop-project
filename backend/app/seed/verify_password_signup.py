import argparse
import asyncio
from uuid import uuid4

from sqlalchemy import delete, func, select

from app.core.security import verify_password
from app.db.session import AsyncSessionLocal
from app.models import Parent, RefreshToken
from app.services.auth import AuthService


async def main() -> None:
    parser = argparse.ArgumentParser(description="Verify local username/password signup persistence.")
    parser.add_argument("--username", default=f"local_test_{uuid4().hex[:8]}")
    parser.add_argument("--password", default="test-password-123")
    parser.add_argument("--nickname", default="Local Test Parent")
    parser.add_argument("--cleanup", action="store_true", help="Delete the created test parent after verification.")
    args = parser.parse_args()

    async with AsyncSessionLocal() as session:
        service = AuthService(session=session)
        auth = await service.password_signup(
            username=args.username,
            password=args.password,
            nickname=args.nickname,
        )

        parent = await session.scalar(
            select(Parent).where(Parent.parent_id == auth["parent"]["parentId"])
        )
        if parent is None:
            raise RuntimeError("Parent was not saved.")

        refresh_count = await session.scalar(
            select(func.count())
            .select_from(RefreshToken)
            .where(RefreshToken.parent_id == parent.parent_id)
        )

        print(
            {
                "saved": True,
                "parent_id": parent.parent_id,
                "username": parent.username,
                "nickname": parent.nickname,
                "provider": parent.provider,
                "kakao_id": parent.kakao_id,
                "password_saved_as_hash": bool(parent.password_hash)
                and parent.password_hash != args.password,
                "password_hash_valid": verify_password(args.password, parent.password_hash or ""),
                "refresh_tokens": refresh_count,
                "is_new_parent": auth["isNewParent"],
            }
        )

        if args.cleanup:
            await session.execute(delete(RefreshToken).where(RefreshToken.parent_id == parent.parent_id))
            await session.execute(delete(Parent).where(Parent.parent_id == parent.parent_id))
            await session.commit()
            print({"cleanup": True, "parent_id": parent.parent_id})


if __name__ == "__main__":
    asyncio.run(main())
