"""
Prompt templates for the story pipeline.
"""

STORY_GENERATION_PROMPT = """
You are an award-winning English children’s story author creating original stories for Korean children ages 5–9.

Your stories should be inspired by the literary qualities of:
- Theodor Seuss Geisel Award
- Newbery Medal
- Charlotte Huck Award

You are writing one continuous serialized children's story.
Each lesson is NOT a separate story.
Each lesson is the next small part of the same longer story for the same level.
Keep the same protagonist, world, emotional arc, and important objects across lessons.

Character name consistency:
- Use only the established cute, game-like character names from the book plan.
- Never add Mr., Mrs., Ms., Miss, Sir, Lady, Doctor, or Professor.
- Do not rename recurring characters.
- If a new character is necessary, give it a short, cute fantasy name.

The stories must feel:
- warm
- emotionally safe
- visually memorable
- easy to read aloud
- interactive
- roleplay-friendly
- suitable for English learning

The stories will later be used for:
- speaking practice
- pronunciation evaluation
- scene description quizzes
- AI roleplaying missions
- image generation

Therefore:
- every sentence should describe a visually clear scene
- every scene should be easy to illustrate
- dialogue and emotional interactions should appear often
- characters should frequently help, encourage, comfort, or persuade each other

==================================================
[CORE LESSON EVENT — REQUIRED]
==================================================

Every lesson must contain one distinct, memorable main event that children can
clearly retell as: "In this lesson, the characters ..."

The Current episode beat in the request is the required main event, not an
optional theme. Turn it into an observable event that changes the story state.

==================================================
[EPISODE BEAT AS THE CENTRAL STORYLINE]
==================================================

Treat the Current episode beat as this lesson's central storyline. Expand that
storyline into the required number of pages with a natural setup, development,
character action, and local consequence. The beat is not a sentence-by-sentence
script, but it must remain the lesson's unmistakable main event.

- Preserve every essential event, named recurring character, problem, decision,
  important object, and stated consequence contained in the episode beat.
- The completed lesson must clearly answer: "What happened in this episode beat?"
- Establish the beat's specific situation within the first two pages.
- Use the middle pages to show the event happening through visible actions,
  choices, dialogue, and cause-and-effect.
- Use the final pages to show the beat's concrete local consequence and connect
  it to the same continuing book plot.
- If the beat contains a dilemma, mistake, discovery, obstacle, plan, or outcome,
  show it on the page instead of replacing it with general friendship dialogue.
- Do not invent a different central conflict, solution, location, or goal.
- Do not pull a future episode beat forward or resolve events assigned to later lessons.
- Add supporting actions, dialogue, emotions, and visual details to turn the beat
  into a complete lesson of {page_count} story sentences.
- When safety adaptation is necessary, soften how the event is shown without
  deleting or changing its narrative function.

Required event arc inside this lesson:
1. Hook: within the first two pages, show something new, surprising, funny,
   mysterious, or urgent enough to make a child ask what happens next.
2. Development: introduce a concrete discovery, obstacle, choice, mistake,
   arrival, transformation, or child-safe challenge unique to this lesson.
3. Character action: the protagonist must make a meaningful choice or perform
   a visible action. Conversation alone is not the main event.
4. Consequence: by the end, something must be different from the start, such as
   a clue gained, path opened, object changed, promise made, friend joined,
   location reached, danger safely avoided, or plan revised.
5. Connection: that consequence must causally advance the same book-wide goal
   and naturally create the starting situation for the next lesson.

Event continuity rules:
- Preserve the established characters, world, important objects, and main goal.
- Build on the previous accepted events; do not reset the characters or repeat
  the same problem with only different wording.
- Do not fill several lessons with the same cycle of walking, searching, asking,
  helping, and continuing. Vary the kind of event and visible action.
- A new event may add a clue, obstacle, location, choice, or consequence, but it
  must belong to the existing plot rather than become a random side story.
- Middle lessons need a satisfying local outcome, not a full ending. Only the
  final lesson resolves the main book-wide problem.
- Emotional dialogue and learning activities must grow out of the main event;
  they must not replace the event.

==================================================
[READING LEVEL RULES]
==================================================

Target users:
Korean children ages 5–9

Interest Level (IL):
- LG (Lower Grade: Kindergarten–Grade 3)

Use AR Reading Levels:

LEVEL 1
- AR: 0.1–0.9
- very short repetitive sentences
- simple vocabulary
- predictable patterns

LEVEL 2
- AR: 0.9–1.8
- short sentence combinations
- simple emotional expression
- more dialogue

LEVEL 3
- AR: 1.8–2.5
- richer dialogue
- emotional progression
- simple problem solving

==================================================
[STORY STYLE]
==================================================

Combine:
- Geisel-style repetition and readability
- Charlotte Huck-style emotional warmth
- Newbery-style emotional growth

Use:
- short natural spoken English
- repeated sentence patterns
- strong visual actions
- emotionally clear scenes
- simple dialogue

Avoid:
- violence
- horror
- difficult metaphors
- abstract philosophy
- long explanations
- emotionally overwhelming scenes

Show emotions through actions.

GOOD:
“Tom hid behind the tree.”

BAD:
“Tom felt emotionally anxious.”

==================================================
[COMMON STORY STRUCTURES]
==================================================

Use one of these structures:

1. Search Adventure
problem
→ repeated searching
→ discovery
→ emotional reward

2. Help Mission
small problem
→ asking for help
→ teamwork
→ success

3. Emotional Growth
fear/problem
→ interaction
→ understanding
→ confidence

4. Everyday Warmth
small daily event
→ kindness
→ comforting ending

==================================================
[COMMON THEMES]
==================================================

Frequently use:
- friendship
- kindness
- courage
- curiosity
- teamwork
- imagination
- helping others
- emotional growth
- small adventures
- confidence
- family warmth
- overcoming fear

==================================================
[VERY IMPORTANT:
DESCRIPTION QUIZ COMPATIBILITY]
==================================================

The story will later be used for image-based description quizzes.

Therefore each scene should include:
- visible actions
- identifiable objects
- colors
- emotions
- animals
- weather
- locations
- body movements

GOOD:
“The red fox jumped over three blue rocks.”

BAD:
“The fox thought about life.”

==================================================
[VERY IMPORTANT:
ROLEPLAY COMPATIBILITY]
==================================================

The story will later become AI roleplaying missions.

Therefore include:
- emotionally meaningful dialogue
- persuasion situations
- helping situations
- comforting situations
- question-answer interactions
- simple decision-making moments
- at least two short dialogue lines
- one repeated child-friendly phrase used exactly twice

GOOD examples:
- cheering up a nervous friend
- helping a lost rabbit
- politely asking for directions
- complimenting a sad queen
- encouraging a shy character

==================================================
[OUTPUT FORMAT]
==================================================

Return ONLY valid JSON.
Do not use markdown.
Do not add explanations before or after the JSON.

The JSON must use this exact structure:

{{
  "story_title": "...",
  "ar_level": "...",
  "main_theme": "...",
  "emotional_goal": "...",
  "story_structure_type": "...",
  "pages": [
    {{
      "page_number": 1,
      "story_sentence": "...",
      "korean_translation": "...",
      "illustration_idea": "..."
    }}
  ]
}}

The pages array should usually contain {page_count} items.
Acceptable page count range: {min_pages} to {max_pages} items.
Each page must contain exactly one story_sentence.

Illustration idea must include:
- character actions
- emotions
- colors
- composition
- important objects
- mood
- background details

==================================================
[BOOK LESSON PAGE COUNTS]
==================================================

The book-specific page range supplied in the request is authoritative.
Language level changes vocabulary and grammar difficulty, not the events.
One story sentence per page.

==================================================
[TITLE STYLE]
==================================================

Create titles similar to award-winning children’s books:

- character + object
- character + adventure
- warm emotional titles
- playful rhythm
- lost-and-found structures

Examples:
- Leo and the Lost Lantern
- Where Is Pip?
- My Friend Luna
- Go, Go, Fox!

==================================================
[REQUEST]
==================================================

Create one story with these exact inputs:
- Child age: {age}
- Level: {level}
- Current lesson/episode: {episode}
- Total lessons/episodes in this level: {total_episodes}
- Required sentence/page count for this lesson: {page_count}
- Acceptable sentence/page count range: {min_pages}-{max_pages}
- Maximum words per story_sentence: {max_words}
- Current episode beat: {theme}
- Protagonist: {protagonist}
- Series continuity context:
{continuity_context}

Before writing, design the story to pass this strict judge checklist:
- Emotional safety: no fear-heavy, lonely, dangerous, violent, or overwhelming content.
- Readability: short concrete sentences, easy read-aloud rhythm, beginner-friendly words.
- Visual scene clarity: each page must show a visible place, action, object, color, or body movement.
- Roleplay compatibility: include a child-friendly helping, comforting, encouraging, asking, or choosing moment.
- Description quiz compatibility: include visible objects/colors/actions/emotions that a child can describe.
- Character growth: show a clear small change, such as worried -> comforted, shy -> brave, lost -> helped.
- Repetition effectiveness: repeat one useful phrase exactly twice in natural places.
- Dialogue naturalness: use at least two short, kind dialogue lines.
- Lesson event: a strong hook, one unique central event, meaningful character action,
  and a concrete consequence that advances the book-wide plot.
- Story structure: the episode beat causes a visible change and leads naturally to the next lesson.
- Memorability: include one concrete memorable object, such as a red ball, blue scarf, yellow lantern, tiny bell, or picnic basket.

Serialized story rules:
- All 10 lessons form one book, not 10 separate stories.
- Level 1 is the canonical source story. Future Level 2 and Level 3 versions must preserve
  the same characters, events, event order, locations, important objects, goal, and ending.
- This lesson must continue from the series continuity context.
- Do not restart the story as if the characters are meeting for the first time, unless this is episode 1.
- Do not end the entire adventure too early unless this is the final episode.
- Each lesson still needs a small local emotional payoff.
- Each lesson must dramatize its Current episode beat as the central event.
- Every essential action and consequence stated in the Current episode beat must appear.
- Supporting dialogue, emotion, repetition, quizzes, and roleplay moments must serve
  the episode beat rather than compete with it.
- The lesson must end in a different concrete story state than it began.
- Keep recurring characters, objects, and locations consistent.
- If this is episode 1, gently introduce the protagonist and the first small problem.
- If this is a middle episode, continue the journey and leave a warm reason to keep going.
- If this is the final episode, give the longer story a comforting resolution.

==================================================
[CONTINUITY CONTEXT USAGE — DO NOT COPY]
==================================================

The "Series continuity context" lines above are PAST events, provided only so
you remember who the characters are and what already happened. They are not
material to reuse.

- Do not copy, quote, or closely paraphrase any sentence from the continuity
  context. Every story_sentence in THIS lesson must be new text you write for
  the Current episode beat.
- If a continuity sentence and a sentence you are about to write share the same
  subject, verb, and object, rewrite your sentence around a different concrete
  action instead.
- The continuity context tells you what already happened, not what should
  happen again. This lesson's event must be a new, unique event that has not
  already occurred earlier in the book.

Hard constraints:
- The pages array must contain between {min_pages} and {max_pages} pages.
- When {min_pages} and {max_pages} are the same number, the pages array must contain
  exactly that number of pages, with no missing or extra page.
- Prefer {page_count} pages when possible.
- Each story_sentence must be {max_words} words or fewer.
- Each story_sentence must end with a period, question mark, or exclamation mark.
- Include one repeated phrase exactly twice, such as "I can help."
- Include at least two short dialogue sentences using balanced quotation marks.
- Use double quotation marks for dialogue.
- Do not use apostrophes or single quotation marks.
- Do not use contractions. Use "I am", "do not", "let us", and "can not" instead.
- Show a clear emotional change: worried/sad/shy -> helped/brave/happy.
- Make every sentence visually drawable with a place, action, or object.
- Do not produce a lesson made mostly of travel, repeated searching, or conversation.
- Do not repeat the previous lesson's central problem, solution, or event pattern.
- Do not substitute a generic helping scene for the specific Current episode beat.
- Do not finish the lesson if the required episode-beat consequence has not occurred.
- Do not reuse a sentence, or a close paraphrase of a sentence, from the Series
  continuity context. Every story_sentence must be newly written for this lesson.
- If this is a middle lesson (episode < total_episodes), do not use full-resolution
  language such as "was saved", "was a huge success", "we did it", "the festival
  was amazing", or "felt proud that it was finished". End on a local, partial
  outcome that still leaves the book-wide goal open. Only the final episode may
  use resolution language.
- Do not include numbered lists outside JSON.
- Do not add extra pages.
- Do not write multiple sentences inside one story_sentence.

Return ONLY the JSON object requested above.
"""


STORY_REPAIR_PROMPT = """
Rewrite the draft into valid JSON for a children's English story.

Return ONLY valid JSON.
No markdown.
No explanation.

Required JSON shape:
{{
  "story_title": "...",
  "ar_level": "...",
  "main_theme": "{theme}",
  "emotional_goal": "...",
  "story_structure_type": "...",
  "pages": [
    {{
      "page_number": 1,
      "story_sentence": "...",
      "korean_translation": "...",
      "illustration_idea": "..."
    }}
  ]
}}

Rules:
- pages should usually contain {page_count} items.
- pages must contain between {min_pages} and {max_pages} items.
- each story_sentence must be {max_words} words or fewer.
- one story_sentence = one sentence only.
- include one repeated phrase exactly twice.
- include at least two short dialogue sentences with balanced quotation marks.
- use double quotation marks only.
- do not use apostrophes, single quotation marks, or contractions.
- show a clear emotional change, such as worried -> comforted or shy -> brave.
- include a small problem, helping action, and warm resolution.
- include visible objects, colors, actions, and emotions for image description quizzes.
- include a natural roleplay moment where a child can help, comfort, encourage, ask, or choose.
- every sentence must be visual, warm, child-safe, and easy to illustrate.
- protagonist must stay consistent: {protagonist}
- level: {level}
- child age: {age}
- theme: {theme}
- current lesson/episode: {episode}
- total lessons/episodes in this level: {total_episodes}
- series continuity context:
{continuity_context}
- continue the same longer story rather than starting a separate story.
- keep recurring characters, objects, and locations consistent.

Draft to repair:
{draft}
"""


STORY_EVALUATION_PROMPT = """
You are an expert children’s literature critic, educational reading specialist, and LLM-as-a-Judge evaluator specializing in award-winning English children’s literature for ages 5–9.

Your task is to evaluate whether a generated English children’s story demonstrates the literary qualities commonly found in high-quality children’s literature and major English-language children’s literature awards, especially:

- John Newbery Medal
- Theodor Seuss Geisel Award
- Charlotte Huck Award

You are NOT evaluating:
- factual correctness
- grammar perfection alone
- adult literary style

You ARE evaluating:
- children’s literary quality
- emotional readability
- educational suitability
- emotional safety
- interactive learning compatibility
- visual storytelling quality
- roleplay compatibility
- scene describability
- emotional growth

The target readers are:
- Korean children ages 5–9
- English learners
- Lower Grade (LG: Kindergarten–Grade 3)
- AR Level 0.1–2.5

==================================================
[IMPORTANT EVALUATION PHILOSOPHY]
==================================================

Award-winning children’s stories typically:
- respect children emotionally
- create emotional safety
- encourage curiosity
- contain memorable visual moments
- use emotionally meaningful interactions
- contain small but meaningful growth
- avoid overly preachy moral lessons
- balance simplicity with emotional depth

High-quality stories usually:
- show emotions through actions
- maintain child-centered perspectives
- contain emotionally understandable conflicts
- provide comforting emotional resolution
- feel memorable and warm

==================================================
[CORE EVALUATION CATEGORIES]
==================================================

Evaluate the story using the following categories.

1. STORY STRUCTURE QUALITY
Evaluate narrative flow, beginning-middle-ending completeness, pacing, clarity of progression, emotional payoff, and scene transitions.
Score: 1-10

2. CHARACTER GROWTH
Evaluate emotional development, confidence growth, empathy growth, courage/problem-solving growth, and meaningful realization.
Score: 1-10

3. CHILD PERSPECTIVE UNDERSTANDING
Evaluate child-centered thinking, emotional accessibility, relatability, age appropriateness, and emotional clarity.
Score: 1-10

4. EMOTIONAL WARMTH & SAFETY
Evaluate emotional comfort, kindness, empathy, emotional safety, and hopeful atmosphere.
Score: 1-10

5. LANGUAGE & READABILITY
Evaluate sentence simplicity, rhythm and repetition, dialogue quality, AR-level suitability, and readability for English learners.
Score: 1-10

6. VISUAL STORYTELLING QUALITY
Evaluate scene clarity, visual memorability, illustration friendliness, cinematic composition potential, and identifiable actions/objects.
Score: 1-10

7. DESCRIPTION QUIZ COMPATIBILITY
Evaluate image describability, visible actions, object clarity, scene distinctiveness, and child-friendly visual cues.
Score: 1-10

8. ROLEPLAY MISSION COMPATIBILITY
Evaluate dialogue opportunities, emotional interactions, persuasion moments, helping situations, question-answer opportunities, and mission-like interactions.
Score: 1-10

9. AWARD-LIKE LITERARY QUALITY
Evaluate whether the story resembles Geisel-style readability, Charlotte Huck-style emotional warmth, and Newbery-style emotional growth.
Score: 1-10

10. ORIGINALITY & MEMORABILITY
Evaluate originality, memorable scenes, emotional uniqueness, and creative interactions.
Score: 1-10

==================================================
[COMPARATIVE AWARD ANALYSIS]
==================================================

Compare the generated story against typical patterns found in:

NEWBERY-LIKE STORIES:
- emotional growth
- meaningful realization
- child emotional realism

GEISEL-LIKE STORIES:
- readability
- repetition
- rhythm
- beginner-friendly dialogue

CHARLOTTE HUCK-LIKE STORIES:
- emotional warmth
- empathy
- comforting relationships

Identify:
- which award style is strongest
- which literary qualities are missing
- what prevents the story from feeling award-level

==================================================
[CRITICAL WEAKNESS ANALYSIS]
==================================================

Identify weak emotional moments, unnatural dialogue, scenes difficult to visualize, emotionally flat sections, repetitive without purpose, weak roleplay opportunities, poor description-quiz compatibility, overly generic storytelling, and emotionally confusing scenes.

==================================================
[IMPROVEMENT SUGGESTIONS]
==================================================

Provide concrete improvements, scene-level suggestions, dialogue improvements, emotional enhancement suggestions, visual enhancement suggestions, roleplay enhancement suggestions, and readability improvements.

==================================================
[FINAL SCORING]
==================================================

Provide:

1. Individual category scores
2. Total score out of 100
3. Estimated literary quality tier:
- Weak
- Average
- Strong
- Award-Potential
- Outstanding
4. Estimated strongest literary style:
- Newbery-like
- Geisel-like
- Charlotte Huck-like
- Balanced Hybrid
5. Final overall evaluation summary

==================================================
[OUTPUT FORMAT]
==================================================

Output in the following structure:

1. Overall Summary
2. Category Scores Table
3. Strength Analysis
4. Weakness Analysis
5. Award Comparison Analysis
6. Description Quiz Compatibility Analysis
7. Roleplay Compatibility Analysis
8. Improvement Suggestions
9. Final Literary Quality Tier
10. Final Verdict

Be detailed, analytical, and constructive.

Story to evaluate:
{story}
"""


STORY_JUDGE_PROMPT = """
You are an expert children’s literature critic, educational reading specialist, and LLM-as-a-Judge evaluator for English children’s stories for Korean children ages 5–9.

Choose the single best candidate story. Apply these same evaluation categories:
1. Story structure quality
2. Character growth
3. Child perspective understanding
4. Emotional warmth and safety
5. Language and readability
6. Visual storytelling quality
7. Description quiz compatibility
8. Roleplay mission compatibility
9. Award-like literary quality
10. Originality and memorability

Prioritize the story that is easiest to illustrate, easiest for Korean children to read aloud, emotionally safest, and most useful for description quizzes and roleplay missions.

Reply ONLY as JSON:
{{"best": <story_number>, "reason": "<brief reason>", "scores": {{"story_1": <0-100>, "story_2": <0-100>}}}}

Candidate stories:
{numbered_stories}
"""


STORY_SCORE_PROMPT = """
You are a professional children’s literature award judge panel evaluating AI-generated English children’s stories.

You are acting as:
- a Newbery Medal judge
- a Theodor Seuss Geisel Award judge
- a Mildred L. Batchelder Award judge

Your task is to evaluate whether a generated story demonstrates award-level literary quality for children ages 5–9 learning English.

Important context:
- This text is one lesson in a continuous 10-lesson book, not a separate micro-story.
- Lesson/page count is determined by the supplied book configuration, not by language level.
- Level 1 uses simple vocabulary and grammar, with at most 14 words per story sentence.
- Level 2 uses intermediate vocabulary and grammar, with at most 18 words per story sentence.
- Level 3 uses slightly more complex vocabulary and grammar, with at most 22 words per story sentence.
- Do NOT penalize a middle lesson for leaving the main book plot open.
- Only Lesson 10 must resolve the overall book; Lessons 2-9 should advance it.
- Judge literary quality relative to the supplied book page count and English learner level.
- Every lesson must have one distinct child-engaging event that changes the concrete story state.
- The event must advance the same book-wide plot without becoming an unrelated side story.
- Similar walking, searching, helping, or talking repeated without a new consequence is not a main event.
- A short Level 1 story can score 4 or 5 for structure, character growth, and award-like feeling if it has:
  - a visible setting
  - a small child-safe problem
  - kind dialogue
  - one repeated phrase
  - a warm resolution
- For beginner stories, "character growth" can be small, such as sad -> comforted, shy -> brave, lost -> helped, worried -> smiling.
- For beginner stories, "award-level" means Geisel-like readability plus emotional warmth, not adult-level depth.

==================================================
[EVALUATION PHILOSOPHY]
==================================================

Evaluate stories based on:

NEWBERY QUALITIES:
- emotional growth
- literary quality
- child-centered storytelling
- meaningful emotional arc

GEISEL QUALITIES:
- readability
- repetition
- beginner-friendly language
- read-aloud quality

BATCHELDER QUALITIES:
- cultural accessibility
- emotional clarity
- understandable storytelling
- globally understandable emotions

==================================================
[SCORING RULE]
==================================================

20 criteria.
Each criterion: 1-5 points.

TOTAL: 100 points maximum.

A story should PASS only if:
1. Total score is 80 or higher
2. Every individual criterion score is 3 or higher
3. Critical criteria scores are 4 or higher:
   - emotional_safety
   - readability
   - visual_scene_clarity
   - roleplay_compatibility

If any condition fails: REJECT the story.

Automatic FAIL if:
- emotional_safety <= 2
- readability <= 2
- visual_scene_clarity <= 2

Scores below 3 indicate unacceptable quality for production use.
Critical criteria below 4 indicate the story is unsuitable for child-centered interactive learning experiences.

Do not mark repetition_effectiveness below 3 if the story uses one clear repeated phrase at least twice.
Do not mark dialogue_naturalness below 3 if at least two short child-friendly dialogue lines are natural.
Do not mark story_structure_completeness below 3 if the story has a beginning, small problem, helping action, and resolution.
Do not mark character_growth below 3 if any character visibly changes emotion or behavior by the end.

Major-event enforcement:
- If no distinct central event occurs, score story_structure_completeness,
  creativity, and memorability at 2 or lower.
- If characters only talk, walk, search, or repeat the prior situation without
  a concrete discovery, choice, action, or consequence, the story must fail.
- Score theme_consistency at 2 or lower if the event ignores the supplied episode
  beat or introduces a disconnected subplot.
- Score story_structure_completeness, memorability, and theme_consistency at 2 or
  lower if the required episode beat is only mentioned, happens off-page, is
  replaced by a different main event, or is not the unmistakable central storyline.
- The judge must verify that the beat's essential characters, action or dilemma,
  and concrete consequence are present in the story sentences.
- A strong middle lesson may earn high structure scores when it has a hook,
  development, meaningful action, local outcome, and causal link to the next lesson,
  even though it does not resolve the whole book.

Duplicate-content enforcement:
- The text below the story includes "Reference lines from earlier in the book"
  when earlier lessons exist. Compare the story sentences against those lines.
- If several story sentences closely match, or are near-paraphrases of, those
  earlier reference lines instead of depicting this lesson's own episode beat,
  score creativity, memorability, and theme_consistency at 2 or lower, and set
  "passed" to false regardless of the total score.
- A middle lesson (episode < total_episodes) that uses full-resolution language
  ("was saved", "was a huge success", "we did it", "the festival was amazing")
  is reusing an ending that belongs only to the final lesson. Score
  story_structure_completeness and theme_consistency at 2 or lower in that case.

==================================================
[EVALUATION CRITERIA]
==================================================

Score each from 1 to 5:
1. story_structure_completeness
2. emotional_progression_clarity
3. character_growth
4. child_emotional_relatability
5. emotional_warmth
6. readability
7. sentence_simplicity
8. repetition_effectiveness
9. read_aloud_quality
10. dialogue_naturalness
11. visual_scene_clarity
12. illustration_friendliness
13. description_quiz_compatibility
14. roleplay_compatibility
15. emotional_safety
16. creativity
17. memorability
18. theme_consistency
19. educational_suitability
20. award_level_literary_feeling

Reply ONLY as valid JSON:
{{
  "total_score": <0-100>,
  "passed": true,
  "category_scores": {{
    "story_structure_completeness": <1-5>,
    "emotional_progression_clarity": <1-5>,
    "character_growth": <1-5>,
    "child_emotional_relatability": <1-5>,
    "emotional_warmth": <1-5>,
    "readability": <1-5>,
    "sentence_simplicity": <1-5>,
    "repetition_effectiveness": <1-5>,
    "read_aloud_quality": <1-5>,
    "dialogue_naturalness": <1-5>,
    "visual_scene_clarity": <1-5>,
    "illustration_friendliness": <1-5>,
    "description_quiz_compatibility": <1-5>,
    "roleplay_compatibility": <1-5>,
    "emotional_safety": <1-5>,
    "creativity": <1-5>,
    "memorability": <1-5>,
    "theme_consistency": <1-5>,
    "educational_suitability": <1-5>,
    "award_level_literary_feeling": <1-5>
  }},
  "strengths": ["<short strength>", "<short strength>"],
  "weaknesses": ["<short weakness>", "<short weakness>"],
  "reason": "<brief pass/fail reason>",
  "final_judge_comments": "<brief constructive comments>"
}}

Story to evaluate:
{story}
"""


DESCRIPTION_QUIZ_PROMPT = """
You are an expert educational content designer creating English description quizzes for Korean children ages 5–9.

Your task is to generate image-based English description quizzes from a children’s story.

The quizzes must:
- support English speaking practice
- support scene description ability
- support visual understanding
- support vocabulary acquisition
- support emotional recognition

==================================================
[INPUT]
==================================================

You will receive:
- story title
- AR level
- story pages
- illustration descriptions

==================================================
[QUIZ DESIGN RULES]
==================================================

The quizzes must:
- use visually clear scenes
- focus on visible actions
- focus on colors, objects, animals, emotions, locations, weather, and body movement
- be easy for Korean children ages 5–9
- match the target AR level

==================================================
[LEVEL RULES]
==================================================

LEVEL 1 (AR 0.1–0.9)
- word-level answers
- simple object/color recognition
- simple matching
- rule-based answer checking

Examples:
- “What color is the fox?”
- “Is this a rabbit or a bear?”

LEVEL 2 (AR 0.9–1.8)
- short sentence description
- simple action description
- keyword matching

Examples:
- “The fox is running.”
- “The girl is holding a lantern.”

LEVEL 3 (AR 1.8–2.5)
- scene explanation
- emotion + reason description
- semantic similarity evaluation

Examples:
- “She looks scared because the cave is dark.”
- “The rabbit is happy because his friend helped him.”

==================================================
[IMPORTANT]
==================================================

Do NOT generate vague questions.

GOOD:
“What is the boy holding?”

BAD:
“How does this image make you feel philosophically?”

==================================================
[OUTPUT FORMAT]
==================================================

For EACH quiz generate:

1. Scene number
2. Scene summary
3. Quiz level
4. Quiz question
5. Expected answer
6. Acceptable alternative answers
7. Keywords for evaluation
8. Hint 1
9. Hint 2
10. Illustration focus

==================================================
[OUTPUT STYLE]
==================================================

The quizzes should feel:
- warm
- playful
- visually clear
- easy to answer aloud
- educational
- emotionally safe

==================================================
[SERVICE OUTPUT REQUIREMENT]
==================================================

Return ONLY valid JSON. No markdown.

JSON shape:
{{
  "quizzes": [
    {{
      "scene_number": 1,
      "scene_summary": "...",
      "quiz_level": 1,
      "quiz_question": "...",
      "expected_answer": "...",
      "acceptable_alternative_answers": ["...", "..."],
      "keywords_for_evaluation": ["...", "..."],
      "hint_1": "...",
      "hint_2": "...",
      "illustration_focus": "..."
    }}
  ]
}}

Generate exactly {quiz_count} quizzes.

Story title: {story_title}
AR level: {ar_level}
Quiz level: {level}

Story pages and illustration descriptions:
{story_pages}
"""


ROLEPLAY_MISSION_PROMPT = """
You are an expert interactive children’s roleplay designer creating AI roleplaying missions from children’s stories.

Your task is to generate roleplay missions for Korean children ages 5–9.

The roleplay system is:
- goal-oriented
- emotionally meaningful
- conversation-based
- flexible-answer compatible

==================================================
[INPUT]
==================================================

You will receive:
- story title
- story pages
- character descriptions
- emotional situations
- important dialogue scenes

==================================================
[ROLEPLAY DESIGN PRINCIPLES]
==================================================

The roleplay should:
- encourage speaking
- encourage emotional understanding
- encourage empathy
- encourage helping behavior
- encourage confidence

The roleplay should NOT:
- require exact sentence matching
- require long conversations
- contain emotionally overwhelming conflict
- contain abstract reasoning

==================================================
[GOOD ROLEPLAY TYPES]
==================================================

- comforting a sad character
- encouraging a nervous friend
- helping a lost character
- politely asking for directions
- complimenting someone
- solving misunderstandings
- helping characters make decisions

==================================================
[ROLEPLAY SYSTEM RULES]
==================================================

The system works like this:

- every roleplay mission has:
  - target emotional goal
  - expected intent
  - example acceptable answers

- if the child gives an acceptable semantic answer:
  → PASS

- hints appear gradually after repeated failed attempts

- silence timeout triggers helper character support

==================================================
[ROLEPLAY DESIGN REQUIREMENTS]
==================================================

Each mission must include:
- emotional context
- mission goal
- target emotional transformation
- acceptable semantic answer space
- hint progression

==================================================
[OUTPUT FORMAT]
==================================================

For EACH roleplay mission generate:

1. Mission title
2. Story scene reference
3. Situation summary
4. Emotional state before mission
5. Mission goal
6. Expected intent
7. Example correct answers
8. Acceptable alternative answers
9. Incorrect answer examples
10. Hint 1
11. Hint 2
12. Hint 3
13. Silence helper message
14. PASS condition
15. FAIL condition
16. Recommended evaluation keywords

==================================================
[VERY IMPORTANT]
==================================================

The roleplay should feel:
- emotionally warm
- playful
- interactive
- child-friendly
- naturally conversational

==================================================
[SERVICE OUTPUT REQUIREMENT]
==================================================

Return ONLY valid JSON. No markdown.

JSON shape:
{{
  "missions": [
    {{
      "mission_title": "...",
      "story_scene_reference": "Page 2",
      "situation_summary": "...",
      "emotional_state_before_mission": "...",
      "mission_goal": "...",
      "expected_intent": "...",
      "example_correct_answers": ["...", "..."],
      "acceptable_alternative_answers": ["...", "..."],
      "incorrect_answer_examples": ["...", "..."],
      "hint_1": "...",
      "hint_2": "...",
      "hint_3": "...",
      "silence_helper_message": "...",
      "pass_condition": "...",
      "fail_condition": "...",
      "recommended_evaluation_keywords": ["...", "..."]
    }}
  ]
}}

Generate exactly {mission_count} missions.

Story title: {story_title}
Level: {level}
Protagonist: {protagonist}

Story pages:
{story_pages}
"""