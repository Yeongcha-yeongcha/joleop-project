from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenException
from app.models import (
    Book,
    ChildProfile,
    CourseType,
    DescriptionQuestion,
    LearningAttempt,
    LearningSession,
    LearningSessionStatus,
    Parent,
    RepeatQuestion,
    RoleplayMessage,
)


class ParentReportService:
    def __init__(self, *, session: AsyncSession) -> None:
        self.session = session

    async def weekly_report(self, *, parent: Parent, profile_id: int, days: int = 7) -> dict:
        profile = await self._owned_profile(parent.parent_id, profile_id)
        today = datetime.now(UTC).date()
        start_date = today - timedelta(days=max(1, days) - 1)
        sessions = await self._completed_sessions(profile.profile_id, start_date)
        session_ids = [session.session_id for session in sessions]
        attempts = await self._attempts(session_ids)
        roleplay_messages = await self._roleplay_messages(session_ids)
        description_questions = await self._description_questions(sessions)
        repeat_questions = await self._repeat_questions(sessions)

        attempts_by_session: dict[int, list[LearningAttempt]] = defaultdict(list)
        for attempt in attempts:
            attempts_by_session[attempt.session_id].append(attempt)

        messages_by_session: dict[int, list[RoleplayMessage]] = defaultdict(list)
        for message in roleplay_messages:
            messages_by_session[message.session_id].append(message)

        daily_reports = []
        attendance_dates = {self._day(session.completed_at) for session in sessions if session.completed_at}
        for offset in range(days):
            current_date = start_date + timedelta(days=offset)
            day_sessions = [
                session for session in sessions
                if session.completed_at and self._day(session.completed_at) == current_date
            ]
            daily_reports.append(
                self._daily_report(
                    current_date=current_date,
                    sessions=day_sessions,
                    attempts_by_session=attempts_by_session,
                    messages_by_session=messages_by_session,
                    description_questions=description_questions,
                    repeat_questions=repeat_questions,
                )
            )

        scored_days = [report for report in daily_reports if report["sessionCount"] > 0]
        average_score = round(
            sum(report["averageScore"] for report in scored_days) / len(scored_days)
        ) if scored_days else None

        return {
            "profile": {
                "profileId": profile.profile_id,
                "nickname": profile.nickname,
                "difficulty": profile.difficulty.value if profile.difficulty else None,
            },
            "range": {
                "from": start_date.isoformat(),
                "to": today.isoformat(),
            },
            "attendanceDates": sorted(day.isoformat() for day in attendance_dates),
            "summary": {
                "averageScore": average_score,
                "completedChapters": len(sessions),
                "comment": self._summary_comment(average_score, len(sessions)),
            },
            "days": daily_reports,
        }

    async def _owned_profile(self, parent_id: int, profile_id: int) -> ChildProfile:
        profile = await self.session.scalar(
            select(ChildProfile).where(
                ChildProfile.parent_id == parent_id,
                ChildProfile.profile_id == profile_id,
                ChildProfile.deleted_at.is_(None),
            )
        )
        if profile is None:
            raise ForbiddenException("해당 프로필에 접근할 수 없습니다.")
        return profile

    async def _completed_sessions(self, profile_id: int, start_date: date) -> list[LearningSession]:
        start_at = datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
        result = await self.session.execute(
            select(LearningSession)
            .options(selectinload(LearningSession.book))
            .where(
                LearningSession.profile_id == profile_id,
                LearningSession.status == LearningSessionStatus.COMPLETED,
                LearningSession.completed_at.is_not(None),
                LearningSession.completed_at >= start_at,
            )
            .order_by(LearningSession.completed_at, LearningSession.session_id)
        )
        return list(result.scalars().all())

    async def _attempts(self, session_ids: list[int]) -> list[LearningAttempt]:
        if not session_ids:
            return []
        result = await self.session.execute(
            select(LearningAttempt)
            .where(LearningAttempt.session_id.in_(session_ids))
            .order_by(LearningAttempt.created_at, LearningAttempt.attempt_id)
        )
        return list(result.scalars().all())

    async def _roleplay_messages(self, session_ids: list[int]) -> list[RoleplayMessage]:
        if not session_ids:
            return []
        result = await self.session.execute(
            select(RoleplayMessage)
            .where(RoleplayMessage.session_id.in_(session_ids))
            .order_by(RoleplayMessage.created_at, RoleplayMessage.message_id)
        )
        return list(result.scalars().all())

    async def _description_questions(self, sessions: list[LearningSession]) -> dict[tuple[int, int, int], DescriptionQuestion]:
        if not sessions:
            return {}
        filters = {(session.book_id, session.chapter_number) for session in sessions}
        result = await self.session.execute(
            select(DescriptionQuestion).where(
                tuple_(DescriptionQuestion.book_id, DescriptionQuestion.chapter_number).in_(filters)
            )
        )
        return {
            (question.book_id, question.chapter_number, question.question_id): question
            for question in result.scalars().all()
        }

    async def _repeat_questions(self, sessions: list[LearningSession]) -> dict[tuple[int, int, int], RepeatQuestion]:
        if not sessions:
            return {}
        filters = {(session.book_id, session.chapter_number) for session in sessions}
        result = await self.session.execute(
            select(RepeatQuestion).where(
                tuple_(RepeatQuestion.book_id, RepeatQuestion.chapter_number).in_(filters)
            )
        )
        return {
            (question.book_id, question.chapter_number, question.question_id): question
            for question in result.scalars().all()
        }

    def _daily_report(
        self,
        *,
        current_date: date,
        sessions: list[LearningSession],
        attempts_by_session: dict[int, list[LearningAttempt]],
        messages_by_session: dict[int, list[RoleplayMessage]],
        description_questions: dict[tuple[int, int, int], DescriptionQuestion],
        repeat_questions: dict[tuple[int, int, int], RepeatQuestion],
    ) -> dict:
        if not sessions:
            return {
                "date": current_date.isoformat(),
                "sessionCount": 0,
                "averageScore": None,
                "learnedWords": [],
                "learnedExpressions": [],
                "strengths": [],
                "needsPractice": [],
                "comment": "아직 완료한 학습이 없습니다.",
            }

        scores: list[int] = []
        repeat_scores: list[int] = []
        description_scores: list[int] = []
        roleplay_scores: list[int] = []
        learned_words: list[str] = []
        learned_expressions: list[str] = []
        books: list[str] = []
        description_questions_by_chapter: dict[tuple[int, int], list[DescriptionQuestion]] = defaultdict(list)
        for (book_id, chapter_number, _), question in description_questions.items():
            description_questions_by_chapter[(book_id, chapter_number)].append(question)

        for session in sessions:
            if isinstance(session.book, Book):
                books.append(session.book.title)
            session_attempts = attempts_by_session.get(session.session_id, [])
            for attempt in session_attempts:
                scores.append(attempt.score)
                if attempt.course_type == CourseType.REPEAT:
                    repeat_scores.append(attempt.score)
                    repeat_question = repeat_questions.get((session.book_id, session.chapter_number, attempt.question_id))
                    if repeat_question:
                        learned_expressions.append(repeat_question.target_text)
                if attempt.course_type == CourseType.DESCRIPTION:
                    description_scores.append(attempt.score)
                    question = description_questions.get((session.book_id, session.chapter_number, attempt.question_id))
                    if question:
                        if question.blank_word:
                            learned_words.append(question.blank_word)
                        expression = question.source_text or question.answer_sentence or question.sentence
                        if expression:
                            learned_expressions.append(expression)
            for message in messages_by_session.get(session.session_id, []):
                if message.score is not None:
                    scores.append(message.score)
                    roleplay_scores.append(message.score)
                transcript = message.user_transcript.strip()
                if transcript and not self._is_mock_transcript(transcript):
                    learned_expressions.append(transcript)
            chapter_description_questions = description_questions_by_chapter.get(
                (session.book_id, session.chapter_number),
                [],
            )
            if not learned_words:
                learned_words.extend(
                    question.blank_word
                    for question in chapter_description_questions
                    if question.blank_word
                )
            if not learned_expressions:
                learned_expressions.extend(
                    question.source_text or question.answer_sentence or question.sentence
                    for question in chapter_description_questions
                    if question.source_text or question.answer_sentence or question.sentence
                )

        average_score = round(sum(scores) / len(scores)) if scores else sessions[-1].total_score
        strengths = self._strengths(repeat_scores, description_scores, roleplay_scores)
        needs_practice = self._needs_practice(repeat_scores, description_scores, roleplay_scores)

        return {
            "date": current_date.isoformat(),
            "sessionCount": len(sessions),
            "averageScore": average_score,
            "books": self._unique(books)[:2],
            "learnedWords": self._unique(learned_words)[:6],
            "learnedExpressions": self._unique(learned_expressions)[:4],
            "strengths": strengths,
            "needsPractice": needs_practice,
            "comment": self._daily_comment(average_score, strengths, needs_practice),
            "breakdown": {
                "repeat": self._average(repeat_scores),
                "description": self._average(description_scores),
                "roleplay": self._average(roleplay_scores),
            },
        }

    @staticmethod
    def _day(value: datetime) -> date:
        return value.astimezone(UTC).date() if value.tzinfo else value.date()

    @staticmethod
    def _average(scores: list[int]) -> int | None:
        return round(sum(scores) / len(scores)) if scores else None

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        seen = set()
        unique = []
        for value in values:
            normalized = value.strip()
            key = normalized.lower()
            if not normalized or key in seen or ParentReportService._is_mock_transcript(normalized):
                continue
            seen.add(key)
            unique.append(normalized)
        return unique

    @staticmethod
    def _is_mock_transcript(value: str) -> bool:
        return value.strip().lower() == "mock transcript"

    def _strengths(self, repeat: list[int], description: list[int], roleplay: list[int]) -> list[str]:
        strengths = []
        if self._average(repeat) is not None and self._average(repeat) >= 80:
            strengths.append("따라 말하기에서 문장을 또렷하게 말했어요.")
        if self._average(description) is not None and self._average(description) >= 80:
            strengths.append("그림 단서를 보고 알맞은 단어를 잘 찾았어요.")
        if self._average(roleplay) is not None and self._average(roleplay) >= 80:
            strengths.append("롤플레잉에서 자신 있게 대답했어요.")
        return strengths or ["학습을 끝까지 완료했어요."]

    def _needs_practice(self, repeat: list[int], description: list[int], roleplay: list[int]) -> list[str]:
        needs = []
        if self._average(repeat) is not None and self._average(repeat) < 70:
            needs.append("따라 말하기에서 발음과 빠뜨린 단어를 다시 연습해보면 좋아요.")
        if self._average(description) is not None and self._average(description) < 70:
            needs.append("묘사 퀴즈에서는 단어를 문장 속에서 말하는 연습이 필요해요.")
        if self._average(roleplay) is not None and self._average(roleplay) < 70:
            needs.append("롤플레잉에서는 조금 더 긴 표현으로 대답해보면 좋아요.")
        return needs

    @staticmethod
    def _daily_comment(score: int | None, strengths: list[str], needs: list[str]) -> str:
        if score is None:
            return "아직 완료한 학습이 없습니다."
        if score >= 85:
            return "오늘은 이야기 단어와 말하기 흐름이 안정적이었어요."
        if score >= 70:
            return "좋은 흐름이에요. 짧게 복습하면 새 표현이 더 오래 남을 거예요."
        return needs[0] if needs else strengths[0]

    @staticmethod
    def _summary_comment(average_score: int | None, completed_chapters: int) -> str:
        if completed_chapters == 0:
            return "이번 기간에는 아직 완료한 챕터가 없습니다."
        if average_score is not None and average_score >= 85:
            return "이번 주는 이해도와 말하기 자신감이 좋아요."
        if average_score is not None and average_score >= 70:
            return "이번 주 학습 흐름이 좋아요. 복습을 더하면 표현이 자연스러워질 거예요."
        return "이번 주는 익숙한 단어부터 가볍게 반복 연습하면 좋아요."
