from app.models import CourseType


class ProgressService:
    COURSE_RANGES: dict[CourseType, tuple[int, int]] = {
        CourseType.READING: (0, 25),
        CourseType.REPEAT: (25, 50),
        CourseType.DESCRIPTION: (50, 75),
        CourseType.ROLEPLAY: (75, 100),
    }

    def course_progress(self, *, current_step: int, total_steps: int) -> int:
        if total_steps <= 0:
            return 0
        return min(100, round(current_step / total_steps * 100))

    def total_progress(
        self,
        *,
        course_type: CourseType,
        current_step: int,
        total_steps: int,
    ) -> int:
        start, end = self.COURSE_RANGES[course_type]
        if total_steps <= 0:
            return start
        course_span = end - start
        return min(end, start + round(current_step / total_steps * course_span))
