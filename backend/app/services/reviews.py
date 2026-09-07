from datetime import UTC, datetime, timedelta
from math import exp, log

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BookNotFoundException, QuestionNotFoundException
from app.models import (
    Book,
    ChildProfile,
    DescriptionQuestion,
    LearningSession,
    LearningSessionStatus,
    ReviewAttempt,
    ReviewCard,
    ReviewCardType,
    ReviewMode,
    ReviewRating,
    RoleplayMission,
)
from app.services.roleplay import AIRoleplayService, MockRoleplayService, clean_roleplay_transcript, roleplay_runtime_context
from app.services.story_talk import StoryTalkService


class ReviewService:
    TARGET_RECALL = 0.85
    INITIAL_INTERVAL_HOURS = 0
    AGAIN_INTERVAL_HOURS = 6
    NEW_GOOD_INTERVAL_HOURS = 24
    NEW_EASY_INTERVAL_HOURS = 72
    MAX_INTERVAL_HOURS = 24 * 120

    SMART_MIX_PLAN = (
        ReviewCardType.WORD,
        ReviewCardType.SENTENCE,
        ReviewCardType.WORD,
        ReviewCardType.SENTENCE,
        ReviewCardType.CHAT,
    )
    ROLEPLAY_KEYWORD_PREFIX = "roleplay:"

    def __init__(self, *, session: AsyncSession) -> None:
        self.session = session
        self.story_talk_service = StoryTalkService()

    async def enqueue_chapter_cards(
        self,
        *,
        profile_id: int,
        book_id: int,
        chapter_number: int,
        due_at: datetime | None = None,
    ) -> int:
        due_at = due_at or datetime.now(UTC)
        questions = (
            await self.session.execute(
                select(DescriptionQuestion)
                .where(
                    DescriptionQuestion.book_id == book_id,
                    DescriptionQuestion.chapter_number == chapter_number,
                )
                .order_by(DescriptionQuestion.step)
            )
        ).scalars().all()

        created = 0
        for question in questions:
            source_sentence = question.source_text or question.answer_sentence or question.sentence
            keyword = question.blank_word or self._keyword_from_sentence(source_sentence or "")
            if not source_sentence or not keyword:
                continue
            cloze_sentence = question.sentence or self._blank_keyword(source_sentence, keyword)
            for card_type in (ReviewCardType.WORD, ReviewCardType.SENTENCE, ReviewCardType.CHAT):
                if await self._create_card_if_missing(
                    profile_id=profile_id,
                    book_id=book_id,
                    chapter_number=chapter_number,
                    card_type=card_type,
                    source_question_id=question.question_id,
                    source_sentence=source_sentence,
                    cloze_sentence=cloze_sentence,
                    keyword=keyword,
                    due_at=due_at,
                ):
                    created += 1

        missions = list((
            await self.session.execute(
                select(RoleplayMission)
                .where(
                    RoleplayMission.book_id == book_id,
                    RoleplayMission.chapter_number == chapter_number,
                )
                .order_by(RoleplayMission.mission_id)
            )
        ).scalars().all())
        for mission in missions:
            context = roleplay_runtime_context(mission)
            if await self._create_card_if_missing(
                profile_id=profile_id,
                book_id=book_id,
                chapter_number=chapter_number,
                card_type=ReviewCardType.CHAT,
                source_question_id=-mission.mission_id,
                source_sentence=context["situation"],
                cloze_sentence=context["opening_message"],
                keyword=f"{self.ROLEPLAY_KEYWORD_PREFIX}{mission.mission_id}",
                due_at=due_at,
            ):
                created += 1
        return created

    async def due_cards(
        self,
        *,
        profile: ChildProfile,
        limit: int = 5,
        mode: ReviewMode = ReviewMode.SMART_MIX,
    ) -> dict:
        now = datetime.now(UTC)
        if mode in {ReviewMode.SMART_MIX, ReviewMode.STORY_TALK}:
            await self._ensure_roleplay_review_cards(profile=profile, now=now)
        cards = await self._due_cards_by_mode(
            profile_id=profile.profile_id,
            limit=limit,
            mode=mode,
            now=now,
        )
        await self._attach_roleplay_payloads(cards)
        return {
            "generatedAt": now.isoformat(),
            "dueCount": await self._due_count(profile.profile_id, now, mode=mode),
            "limit": limit,
            "mode": mode.value,
            "memoryScore": await self.memory_score(profile_id=profile.profile_id, now=now),
            "cards": [self.card_response(card, now=now) for card in cards],
        }

    async def summary(self, *, profile: ChildProfile) -> dict:
        now = datetime.now(UTC)
        total_count = await self.session.scalar(
            select(func.count()).select_from(ReviewCard).where(ReviewCard.profile_id == profile.profile_id)
        )
        chapters = (
            await self.session.execute(
                select(ReviewCard.book_id, ReviewCard.chapter_number)
                .where(ReviewCard.profile_id == profile.profile_id)
                .group_by(ReviewCard.book_id, ReviewCard.chapter_number)
                .order_by(ReviewCard.book_id, ReviewCard.chapter_number)
            )
        ).all()
        return {
            "dueCount": await self._due_count(profile.profile_id, now),
            "totalCount": total_count or 0,
            "memoryScore": await self.memory_score(profile_id=profile.profile_id, now=now),
            "chapters": [
                {"bookId": book_id, "chapterNumber": chapter_number}
                for book_id, chapter_number in chapters
            ],
            "modes": [
                {
                    "mode": ReviewMode.SMART_MIX.value,
                    "title": "Start Smart Mix",
                    "description": "Word games, sentence quests, and story talk together.",
                },
                {
                    "mode": ReviewMode.WORD_PLAYGROUND.value,
                    "title": "Word Playground",
                    "description": "Spelling, matching cards, and word finding.",
                },
                {
                    "mode": ReviewMode.SENTENCE_QUEST.value,
                    "title": "Sentence Quest",
                    "description": "Missing words, word order, and speaking practice.",
                },
                {
                    "mode": ReviewMode.STORY_TALK.value,
                    "title": "Story Talk",
                    "description": "Talk about the story using your review words.",
                },
            ],
        }

    async def story_talk_prompt(self, *, profile: ChildProfile, limit: int = 5) -> dict:
        now = datetime.now(UTC)
        await self._ensure_roleplay_review_cards(profile=profile, now=now)
        cards = await self._due_cards_by_mode(
            profile_id=profile.profile_id,
            limit=limit,
            mode=ReviewMode.STORY_TALK,
            now=now,
        )
        if not cards:
            cards = await self._recent_cards(
                profile_id=profile.profile_id,
                limit=limit,
                card_types=[ReviewCardType.CHAT],
                roleplay_only=True,
            )
        await self._attach_roleplay_payloads(cards)
        return {
            "mode": ReviewMode.STORY_TALK.value,
            "topic": self._fallback_story_topic(cards),
            "cards": [self.card_response(card, now=now) for card in cards],
        }

    async def story_roleplay_reply(
        self,
        *,
        profile: ChildProfile,
        card_id: int,
        message: str,
        history: list[dict],
    ) -> dict:
        card = await self.session.scalar(
            select(ReviewCard).where(
                ReviewCard.profile_id == profile.profile_id,
                ReviewCard.card_id == card_id,
                ReviewCard.card_type == ReviewCardType.CHAT,
            )
        )
        if not card:
            raise QuestionNotFoundException()
        mission_id = self._roleplay_mission_id(card)
        if mission_id is None:
            raise QuestionNotFoundException()
        mission = await self.session.scalar(
            select(RoleplayMission).where(RoleplayMission.mission_id == mission_id)
        )
        if not mission:
            raise QuestionNotFoundException()

        transcript = clean_roleplay_transcript(mission, message)
        turn = min(len(history) + 1, roleplay_runtime_context(mission)["required_turns"])
        service = AIRoleplayService(session=self.session)
        try:
            result = await service.respond(
                mission=mission,
                session_id=-card.card_id,
                transcript=transcript,
                turn=turn,
                history=history,
            )
        except Exception:
            result = await MockRoleplayService().respond(
                mission=mission,
                session_id=-card.card_id,
                transcript=transcript,
                turn=turn,
            )
        required_turns = roleplay_runtime_context(mission)["required_turns"]
        return {
            "userTranscript": transcript,
            "characterText": result.get("text") or "Great job. Keep going.",
            "score": result.get("score", 70),
            "source": result.get("source", "llm"),
            "missionCompleted": turn >= required_turns,
            "card": self.card_response(card, now=datetime.now(UTC)),
        }

    async def story_talk_reply(
        self,
        *,
        profile: ChildProfile,
        card_ids: list[int],
        message: str,
    ) -> dict:
        cards = list((
            await self.session.execute(
                select(ReviewCard)
                .options(selectinload(ReviewCard.book))
                .where(
                    ReviewCard.profile_id == profile.profile_id,
                    ReviewCard.card_id.in_(card_ids),
                )
                .order_by(ReviewCard.card_id)
            )
        ).scalars().all())
        if not cards:
            raise QuestionNotFoundException()
        result = await self.story_talk_service.reply(cards=cards, child_message=message)
        return {
            **result,
            "cards": [self.card_response(card, now=datetime.now(UTC)) for card in cards],
        }

    async def record_attempt(
        self,
        *,
        profile: ChildProfile,
        card_id: int,
        rating: ReviewRating,
        correct: bool,
        score: int,
    ) -> dict:
        card = await self.session.scalar(
            select(ReviewCard)
            .where(ReviewCard.card_id == card_id, ReviewCard.profile_id == profile.profile_id)
            .with_for_update()
        )
        if not card:
            raise QuestionNotFoundException()

        now = datetime.now(UTC)
        memory_before = self.retention_score(card, now)
        interval_hours, ease_factor = self.next_interval(card, rating=rating, correct=correct)
        memory_strength_days = self.memory_strength_days(interval_hours)
        next_review_at = now + timedelta(hours=interval_hours)

        card.interval_hours = interval_hours
        card.ease_factor = ease_factor
        card.memory_strength_days = memory_strength_days
        card.review_count += 1
        if not correct or rating == ReviewRating.AGAIN:
            card.lapse_count += 1
        card.last_reviewed_at = now
        card.next_review_at = next_review_at

        memory_after = self.retention_score(card, now)
        attempt = ReviewAttempt(
            card_id=card.card_id,
            profile_id=profile.profile_id,
            rating=rating,
            correct=correct,
            score=score,
            memory_before=memory_before,
            memory_after=memory_after,
            next_review_at=next_review_at,
        )
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(card)
        return {
            "card": self.card_response(card, now=now),
            "attempt": {
                "rating": rating.value,
                "correct": correct,
                "score": score,
                "memoryBefore": memory_before,
                "memoryAfter": memory_after,
                "nextReviewAt": next_review_at.isoformat(),
            },
        }

    async def seed_chapter_for_profile(
        self,
        *,
        profile: ChildProfile,
        book_id: int,
        chapter_number: int,
    ) -> dict:
        book = await self.session.scalar(select(Book).where(Book.book_id == book_id))
        if not book:
            raise BookNotFoundException()
        created = await self.enqueue_chapter_cards(
            profile_id=profile.profile_id,
            book_id=book_id,
            chapter_number=chapter_number,
        )
        await self.session.commit()
        return {
            "bookId": book_id,
            "chapterNumber": chapter_number,
            "createdCards": created,
        }

    def next_interval(
        self,
        card: ReviewCard,
        *,
        rating: ReviewRating,
        correct: bool,
    ) -> tuple[int, int]:
        ease = card.ease_factor
        if not correct or rating == ReviewRating.AGAIN:
            return self.AGAIN_INTERVAL_HOURS, max(130, ease - 24)
        if card.review_count == 0:
            if rating == ReviewRating.EASY:
                return self.NEW_EASY_INTERVAL_HOURS, min(330, ease + 15)
            return self.NEW_GOOD_INTERVAL_HOURS, ease

        growth = ease / 100
        if rating == ReviewRating.EASY:
            interval = round(max(card.interval_hours, 24) * growth * 1.55)
            ease = min(330, ease + 12)
        else:
            interval = round(max(card.interval_hours, 24) * growth)
            ease = max(130, ease - 4)
        return min(max(interval, 24), self.MAX_INTERVAL_HOURS), ease

    def retention_score(self, card: ReviewCard, now: datetime) -> int:
        reviewed_at = card.last_reviewed_at or card.created_at
        elapsed_days = max(0.0, (now - reviewed_at).total_seconds() / 86400)
        strength = max(card.memory_strength_days, 0.1)
        return round(max(0.0, min(1.0, exp(-elapsed_days / strength))) * 100)

    def memory_strength_days(self, interval_hours: int) -> float:
        interval_days = max(interval_hours / 24, 0.25)
        return interval_days / -log(self.TARGET_RECALL)

    async def memory_score(self, *, profile_id: int, now: datetime) -> int:
        cards = (
            await self.session.execute(
                select(ReviewCard).where(ReviewCard.profile_id == profile_id)
            )
        ).scalars().all()
        if not cards:
            return 100
        return round(sum(self.retention_score(card, now) for card in cards) / len(cards))

    async def _create_card_if_missing(
        self,
        *,
        profile_id: int,
        book_id: int,
        chapter_number: int,
        card_type: ReviewCardType,
        source_question_id: int,
        source_sentence: str,
        cloze_sentence: str,
        keyword: str,
        due_at: datetime,
    ) -> bool:
        existing = await self.session.scalar(
            select(ReviewCard).where(
                ReviewCard.profile_id == profile_id,
                ReviewCard.book_id == book_id,
                ReviewCard.chapter_number == chapter_number,
                ReviewCard.card_type == card_type,
                ReviewCard.source_question_id == source_question_id,
            )
        )
        if existing:
            return False
        self.session.add(
            ReviewCard(
                profile_id=profile_id,
                book_id=book_id,
                chapter_number=chapter_number,
                card_type=card_type,
                source_question_id=source_question_id,
                source_sentence=source_sentence,
                cloze_sentence=cloze_sentence,
                keyword=keyword,
                memory_strength_days=1.0,
                interval_hours=self.INITIAL_INTERVAL_HOURS,
                ease_factor=250,
                review_count=0,
                lapse_count=0,
                next_review_at=due_at,
            )
        )
        return True

    async def _due_cards_by_mode(
        self,
        *,
        profile_id: int,
        limit: int,
        mode: ReviewMode,
        now: datetime,
    ) -> list[ReviewCard]:
        if mode == ReviewMode.SMART_MIX:
            return await self._smart_mix_cards(profile_id=profile_id, limit=limit, now=now)
        card_types = {
            ReviewMode.WORD_PLAYGROUND: [ReviewCardType.WORD],
            ReviewMode.SENTENCE_QUEST: [ReviewCardType.SENTENCE],
            ReviewMode.STORY_TALK: [ReviewCardType.CHAT],
        }[mode]
        return await self._due_cards(
            profile_id=profile_id,
            limit=limit,
            now=now,
            card_types=card_types,
            roleplay_only=mode == ReviewMode.STORY_TALK,
        )

    async def _smart_mix_cards(self, *, profile_id: int, limit: int, now: datetime) -> list[ReviewCard]:
        selected: list[ReviewCard] = []
        seen: set[int] = set()
        seen_sources: set[int] = set()
        for card_type in self.SMART_MIX_PLAN[:limit]:
            card = await self._first_review_card(
                profile_id=profile_id,
                now=now,
                card_type=card_type,
                exclude_ids=seen,
                exclude_source_question_ids=seen_sources,
                roleplay_only=card_type == ReviewCardType.CHAT,
            )
            if card:
                selected.append(card)
                seen.add(card.card_id)
                if card.source_question_id is not None:
                    seen_sources.add(card.source_question_id)
        if len(selected) < limit:
            rest = await self._review_cards(
                profile_id=profile_id,
                limit=limit - len(selected),
                now=now,
                card_types=[ReviewCardType.WORD, ReviewCardType.SENTENCE],
                exclude_ids=seen,
                exclude_source_question_ids=seen_sources,
            )
            selected.extend(rest)
        return selected

    async def _first_review_card(
        self,
        *,
        profile_id: int,
        now: datetime,
        card_type: ReviewCardType,
        exclude_ids: set[int],
        exclude_source_question_ids: set[int],
        roleplay_only: bool = False,
    ) -> ReviewCard | None:
        stmt = (
            select(ReviewCard)
            .options(selectinload(ReviewCard.book))
            .where(
                ReviewCard.profile_id == profile_id,
                ReviewCard.card_type == card_type,
            )
            .order_by(ReviewCard.next_review_at, ReviewCard.card_id)
            .limit(1)
        )
        if exclude_ids:
            stmt = stmt.where(ReviewCard.card_id.not_in(exclude_ids))
        if exclude_source_question_ids:
            stmt = stmt.where(ReviewCard.source_question_id.not_in(exclude_source_question_ids))
        if roleplay_only:
            stmt = stmt.where(ReviewCard.keyword.like(f"{self.ROLEPLAY_KEYWORD_PREFIX}%"))
        return await self.session.scalar(stmt)

    async def _due_cards(
        self,
        *,
        profile_id: int,
        limit: int,
        now: datetime,
        card_types: list[ReviewCardType] | None = None,
        exclude_ids: set[int] | None = None,
        exclude_source_question_ids: set[int] | None = None,
        roleplay_only: bool = False,
    ) -> list[ReviewCard]:
        stmt = (
            select(ReviewCard)
            .options(selectinload(ReviewCard.book))
            .where(
                ReviewCard.profile_id == profile_id,
                ReviewCard.next_review_at <= now,
            )
            .order_by(ReviewCard.next_review_at, ReviewCard.card_id)
            .limit(limit * 4)
        )
        if card_types:
            stmt = stmt.where(ReviewCard.card_type.in_(card_types))
        if roleplay_only:
            stmt = stmt.where(ReviewCard.keyword.like(f"{self.ROLEPLAY_KEYWORD_PREFIX}%"))
        if exclude_ids:
            stmt = stmt.where(ReviewCard.card_id.not_in(exclude_ids))
        due_cards = self._diverse_cards(
            list((await self.session.execute(stmt)).scalars().all()),
            limit=limit,
            exclude_source_question_ids=exclude_source_question_ids,
        )
        if len(due_cards) >= limit:
            return due_cards
        seen = {card.card_id for card in due_cards}
        if exclude_ids:
            seen.update(exclude_ids)
        seen_sources = {card.source_question_id for card in due_cards if card.source_question_id is not None}
        if exclude_source_question_ids:
            seen_sources.update(exclude_source_question_ids)
        upcoming_cards = await self._review_cards(
            profile_id=profile_id,
            limit=limit - len(due_cards),
            now=now,
            card_types=card_types,
            exclude_ids=seen,
            exclude_source_question_ids=seen_sources,
            roleplay_only=roleplay_only,
        )
        return due_cards + upcoming_cards

    async def _review_cards(
        self,
        *,
        profile_id: int,
        limit: int,
        now: datetime,
        card_types: list[ReviewCardType] | None = None,
        exclude_ids: set[int] | None = None,
        exclude_source_question_ids: set[int] | None = None,
        roleplay_only: bool = False,
    ) -> list[ReviewCard]:
        stmt = (
            select(ReviewCard)
            .options(selectinload(ReviewCard.book))
            .where(ReviewCard.profile_id == profile_id)
            .order_by(ReviewCard.next_review_at, ReviewCard.card_id)
            .limit(limit * 4)
        )
        if card_types:
            stmt = stmt.where(ReviewCard.card_type.in_(card_types))
        if roleplay_only:
            stmt = stmt.where(ReviewCard.keyword.like(f"{self.ROLEPLAY_KEYWORD_PREFIX}%"))
        if exclude_ids:
            stmt = stmt.where(ReviewCard.card_id.not_in(exclude_ids))
        return self._diverse_cards(
            list((await self.session.execute(stmt)).scalars().all()),
            limit=limit,
            exclude_source_question_ids=exclude_source_question_ids,
        )

    @staticmethod
    def _diverse_cards(
        cards: list[ReviewCard],
        *,
        limit: int,
        exclude_source_question_ids: set[int] | None = None,
    ) -> list[ReviewCard]:
        excluded_sources = exclude_source_question_ids or set()
        selected: list[ReviewCard] = []
        deferred: list[ReviewCard] = []
        seen_sources: set[int] = set()
        for card in cards:
            source_id = card.source_question_id
            if source_id is not None and source_id in excluded_sources:
                deferred.append(card)
                continue
            if source_id is not None and source_id in seen_sources:
                deferred.append(card)
                continue
            selected.append(card)
            if source_id is not None:
                seen_sources.add(source_id)
            if len(selected) >= limit:
                return selected
        for card in deferred:
            if card not in selected:
                selected.append(card)
            if len(selected) >= limit:
                break
        return selected

    async def _recent_cards(
        self,
        *,
        profile_id: int,
        limit: int,
        card_types: list[ReviewCardType] | None = None,
        roleplay_only: bool = False,
    ) -> list[ReviewCard]:
        stmt = (
            select(ReviewCard)
            .options(selectinload(ReviewCard.book))
            .where(ReviewCard.profile_id == profile_id)
            .order_by(ReviewCard.created_at.desc(), ReviewCard.card_id.desc())
            .limit(limit)
        )
        if card_types:
            stmt = stmt.where(ReviewCard.card_type.in_(card_types))
        if roleplay_only:
            stmt = stmt.where(ReviewCard.keyword.like(f"{self.ROLEPLAY_KEYWORD_PREFIX}%"))
        return list((
            await self.session.execute(stmt)
        ).scalars().all())

    async def _due_count(
        self,
        profile_id: int,
        now: datetime,
        mode: ReviewMode = ReviewMode.SMART_MIX,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(ReviewCard)
            .where(ReviewCard.profile_id == profile_id, ReviewCard.next_review_at <= now)
        )
        if mode == ReviewMode.WORD_PLAYGROUND:
            stmt = stmt.where(ReviewCard.card_type == ReviewCardType.WORD)
        elif mode == ReviewMode.SENTENCE_QUEST:
            stmt = stmt.where(ReviewCard.card_type == ReviewCardType.SENTENCE)
        elif mode == ReviewMode.STORY_TALK:
            stmt = stmt.where(
                ReviewCard.card_type == ReviewCardType.CHAT,
                ReviewCard.keyword.like(f"{self.ROLEPLAY_KEYWORD_PREFIX}%"),
            )
        return await self.session.scalar(stmt) or 0

    def card_response(self, card: ReviewCard, *, now: datetime) -> dict:
        response = {
            "cardId": card.card_id,
            "bookId": card.book_id,
            "bookTitle": card.book.title if card.book else "",
            "chapterNumber": card.chapter_number,
            "cardType": card.card_type.value,
            "sourceSentence": card.source_sentence,
            "clozeSentence": card.cloze_sentence,
            "keyword": card.keyword,
            "memoryScore": self.retention_score(card, now),
            "reviewCount": card.review_count,
            "nextReviewAt": card.next_review_at.isoformat(),
        }
        roleplay = getattr(card, "_roleplay_payload", None)
        if roleplay:
            response["roleplayMissionId"] = roleplay["missionId"]
            response["roleplay"] = roleplay
        return response

    async def _attach_roleplay_payloads(self, cards: list[ReviewCard]) -> None:
        mission_ids = [mission_id for card in cards if (mission_id := self._roleplay_mission_id(card)) is not None]
        if not mission_ids:
            return
        missions = {
            mission.mission_id: mission
            for mission in (
                await self.session.execute(
                    select(RoleplayMission).where(RoleplayMission.mission_id.in_(mission_ids))
                )
            ).scalars().all()
        }
        for card in cards:
            mission_id = self._roleplay_mission_id(card)
            mission = missions.get(mission_id) if mission_id is not None else None
            if not mission:
                continue
            context = roleplay_runtime_context(mission)
            card._roleplay_payload = {
                "missionId": mission.mission_id,
                "title": mission.title,
                "description": context["situation"],
                "openingMessage": context["opening_message"],
                "playerGoal": context["player_goal"],
                "childRole": context["child_role"],
                "aiCharacter": context["ai_character"],
                "requiredTurns": context["required_turns"],
                "hints": mission.hint_sequence or [],
                "imageUrl": mission.character_image_url,
            }

    async def _ensure_roleplay_review_cards(self, *, profile: ChildProfile, now: datetime) -> None:
        completed_sessions = list((
            await self.session.execute(
                select(LearningSession.book_id, LearningSession.chapter_number)
                .where(
                    LearningSession.profile_id == profile.profile_id,
                    LearningSession.status == LearningSessionStatus.COMPLETED,
                )
                .group_by(LearningSession.book_id, LearningSession.chapter_number)
            )
        ).all())
        created = 0
        for book_id, chapter_number in completed_sessions:
            missions = list((
                await self.session.execute(
                    select(RoleplayMission).where(
                        RoleplayMission.book_id == book_id,
                        RoleplayMission.chapter_number == chapter_number,
                    )
                )
            ).scalars().all())
            for mission in missions:
                context = roleplay_runtime_context(mission)
                if await self._create_card_if_missing(
                    profile_id=profile.profile_id,
                    book_id=book_id,
                    chapter_number=chapter_number,
                    card_type=ReviewCardType.CHAT,
                    source_question_id=-mission.mission_id,
                    source_sentence=context["situation"],
                    cloze_sentence=context["opening_message"],
                    keyword=f"{self.ROLEPLAY_KEYWORD_PREFIX}{mission.mission_id}",
                    due_at=now,
                ):
                    created += 1
        if created:
            await self.session.commit()

    def _roleplay_mission_id(self, card: ReviewCard) -> int | None:
        if not card.keyword.startswith(self.ROLEPLAY_KEYWORD_PREFIX):
            return None
        try:
            return int(card.keyword.removeprefix(self.ROLEPLAY_KEYWORD_PREFIX))
        except ValueError:
            return None

    @staticmethod
    def _fallback_story_topic(cards: list[ReviewCard]) -> dict:
        if not cards:
            return {
                "title": "Story Talk",
                "opening": "Tell me one thing you remember from your story.",
                "targetWords": [],
                "starterQuestions": [
                    "Who was in the story?",
                    "What happened first?",
                    "What did you like?",
                ],
            }
        keywords = list(dict.fromkeys(card.keyword for card in cards if card.keyword))[:5]
        sentence = cards[0].source_sentence
        return {
            "title": "Story Talk",
            "opening": f"Let's talk about this story moment: {sentence}",
            "targetWords": keywords,
            "starterQuestions": [
                f"What do you remember about {keywords[0]}?" if keywords else "What do you remember?",
                "What happened in this chapter?",
                "Can you say it in your own words?",
            ],
        }

    @staticmethod
    def _blank_keyword(sentence: str, keyword: str) -> str:
        return sentence.replace(keyword, "____", 1)

    @staticmethod
    def _keyword_from_sentence(sentence: str) -> str:
        words = [word.strip(".,!?;:'\"").lower() for word in sentence.split()]
        words = [word for word in words if len(word) >= 4]
        return words[-1] if words else ""
