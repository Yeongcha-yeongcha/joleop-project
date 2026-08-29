/**
 * API 클라이언트
 *
 * VITE_API_BASE_URL 환경 변수가 설정되면 실제 API를,
 * 없으면 src/data/ 목업 데이터를 자동으로 사용합니다.
 *
 * 연동 방법:
 *   1. .env.example → .env.local 복사
 *   2. VITE_API_BASE_URL=http://백엔드주소 설정
 *   3. npm run dev
 */

import type { Book, Lesson, UserStats } from '../types'
import { BOOKS } from '../data/books'
import { LESSONS } from '../data/lessons'

const BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''
const KAKAO_CLIENT_ID: string = import.meta.env.VITE_KAKAO_CLIENT_ID ?? ''
const KAKAO_REDIRECT_URI: string = import.meta.env.VITE_KAKAO_REDIRECT_URI ?? `${window.location.origin}/oauth/kakao/callback`
const ONBOARDING_RESULT_KEY = 'yeongcha:onboarding-result'
const PARENT_TOKEN_KEY = 'yeongcha:parent-access-token'
const PROFILE_TOKEN_KEY = 'yeongcha:profile-access-token'
const MOCK_PARENT_KEY = 'yeongcha:mock-parent'
const MOCK_PROFILES_KEY = 'yeongcha:mock-profiles'

type Difficulty = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED'

interface ApiEnvelope<T> {
  success?: boolean
  data?: T
  error?: {
    code?: string
    message?: string
  }
}

interface BackendBookListData {
  books: BackendBook[]
}

interface BackendHomeData {
  profile: {
    profileId: number
    nickname: string
    difficulty?: Difficulty | null
  }
  status: {
    streakDays: number
    hearts: number
    energy: number
    maxEnergy: number
  }
  currentBook?: BackendCurrentBook | null
}

interface BackendCurrentBook {
  bookId: number
  title: string
  coverImageUrl?: string | null
  lessonName?: string | null
  progress: number
  canResume: boolean
}

interface BackendBook {
  bookId: number
  title: string
  coverImageUrl?: string | null
  difficulty?: Difficulty | null
  locked: boolean
  completed: boolean
  progress: number
}

export class ApiError extends Error {
  status: number
  code?: string

  constructor(message: string, options: { status: number; code?: string }) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status
    this.code = options.code
  }
}

function unwrap<T>(json: T | ApiEnvelope<T>): T {
  if (
    json &&
    typeof json === 'object' &&
    'success' in json &&
    'data' in json
  ) {
    return (json as ApiEnvelope<T>).data as T
  }
  return json as T
}

function authHeaders(token?: string | null): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function parseResponseBody(res: Response): Promise<unknown> {
  const text = await res.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

async function handleResponse<T>(res: Response, method: string, path: string): Promise<T> {
  const body = await parseResponseBody(res)
  if (!res.ok) {
    const envelope = body as ApiEnvelope<T> | null
    const errorMessage = envelope?.error?.message ?? `${method} ${path} → ${res.status}`
    const errorCode = envelope?.error?.code
    throw new ApiError(errorMessage, { status: res.status, code: errorCode })
  }
  return unwrap(body as T | ApiEnvelope<T>)
}

async function get<T>(path: string, token?: string | null): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: authHeaders(token),
  })
  return handleResponse(res, 'GET', path)
}

async function post<T>(path: string, body: unknown, token?: string | null): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
    body: JSON.stringify(body),
  })
  return handleResponse(res, 'POST', path)
}

async function patch<T>(path: string, body: unknown, token?: string | null): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
    body: JSON.stringify(body),
  })
  return handleResponse(res, 'PATCH', path)
}

async function del<T>(path: string, token?: string | null): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })
  return handleResponse(res, 'DELETE', path)
}

export function getParentToken(): string | null {
  return window.localStorage.getItem(PARENT_TOKEN_KEY)
}

export function getProfileToken(): string | null {
  return window.localStorage.getItem(PROFILE_TOKEN_KEY)
}

function saveParentSession(data: ParentAuthData) {
  window.localStorage.setItem(PARENT_TOKEN_KEY, data.parentAccessToken)
  window.localStorage.setItem('yeongcha:refresh-token', data.refreshToken)
}

function saveProfileSession(data: ProfileLoginData) {
  window.localStorage.setItem(PROFILE_TOKEN_KEY, data.profileAccessToken)
  window.localStorage.setItem('yeongcha:active-profile', JSON.stringify(data.profile))
}

function mockProfiles(): ChildProfile[] {
  const raw = window.localStorage.getItem(MOCK_PROFILES_KEY)
  return raw ? JSON.parse(raw) : []
}

function saveMockProfiles(profiles: ChildProfile[]) {
  window.localStorage.setItem(MOCK_PROFILES_KEY, JSON.stringify(profiles))
}

function profileImageUrl(id?: number | null): string {
  const imageId = id ?? Math.floor(Math.random() * 6) + 1
  const assets = [
    '/images/onboarding/lion-wave.png',
    '/images/onboarding/lion-thinking.png',
    '/images/onboarding/lion-backpack.png',
    '/images/onboarding/lion-flag.png',
    '/images/onboarding/lion-reading.png',
    '/images/onboarding/lion-headphones.png',
  ]
  return assets[(imageId - 1) % assets.length]
}

// ─── 사용자 통계  GET /users/me/stats ───────────────────

export async function fetchUserStats(): Promise<UserStats> {
  if (BASE_URL && getProfileToken()) return get('/users/me/stats', getProfileToken())
  return { streak: 15, hearts: 210, xpPercent: 0.7 }
}

export async function fetchHome(): Promise<{ currentBook: Book | null; stats: UserStats }> {
  if (BASE_URL && getProfileToken()) {
    const data = await get<BackendHomeData>('/home', getProfileToken())
    const maxEnergy = data.status.maxEnergy || 1
    return {
      currentBook: data.currentBook ? toFrontendCurrentBook(data.currentBook) : null,
      stats: {
        streak: data.status.streakDays,
        hearts: data.status.hearts,
        xpPercent: data.status.energy / maxEnergy,
      },
    }
  }
  return { currentBook: BOOKS.find((book) => book.status === 'reading') ?? null, stats: await fetchUserStats() }
}

// ─── 책 목록  GET /books ────────────────────────────────

export async function fetchBooks(): Promise<Book[]> {
  if (BASE_URL && getProfileToken()) {
    const data = await get<BackendBookListData>('/books', getProfileToken())
    return mergeBooksWithLocalSamples(data.books.map(toFrontendBook))
  }
  return BOOKS
}

function normalizeBookTitle(title: string): string {
  return title.toLowerCase().replace(/^the\s+/, '').replace(/[^a-z0-9]/g, '')
}

function localBookFor(book: Book): Book | undefined {
  const normalizedTitle = normalizeBookTitle(book.title)
  return BOOKS.find((localBook) => (
    localBook.id === book.id ||
    normalizeBookTitle(localBook.title) === normalizedTitle
  ))
}

function mergeBooksWithLocalSamples(backendBooks: Book[]): Book[] {
  const hydratedBooks = backendBooks.map((book) => {
    const localBook = localBookFor(book)
    if (!localBook) return book
    return {
      ...localBook,
      ...book,
      title: localBook.title,
      coverColor: localBook.coverColor,
      coverImage: book.coverImage ?? localBook.coverImage,
      totalLessons: localBook.totalLessons,
      currentText: book.currentText ?? localBook.currentText,
    }
  })

  const hydratedKeys = new Set(hydratedBooks.map((book) => normalizeBookTitle(book.title)))
  return [
    ...hydratedBooks,
    ...BOOKS.filter((book) => !hydratedKeys.has(normalizeBookTitle(book.title))),
  ]
}

function publicCoverImageUrl(url?: string | null): string | undefined {
  if (!url) return undefined
  const publicImagesIndex = url.indexOf("/frontend/public/images/")
  if (publicImagesIndex >= 0) {
    return `/images/${url.slice(publicImagesIndex + "/frontend/public/images/".length)}`
  }
  return url
}

function toFrontendBook(book: BackendBook): Book {
  const levelByDifficulty: Record<Difficulty, number> = {
    BEGINNER: 1,
    INTERMEDIATE: 2,
    ADVANCED: 3,
  }
  const progress = Math.max(0, Math.min(1, book.progress / 100))
  return {
    id: String(book.bookId),
    title: book.title,
    coverColor: '#ffbd54',
    coverImage: publicCoverImageUrl(book.coverImageUrl),
    level: book.difficulty ? levelByDifficulty[book.difficulty] : 1,
    totalLessons: 4,
    currentLesson: Math.max(1, Math.min(4, Math.floor(progress * 4) + 1)),
    progress,
    status: book.locked ? 'locked' : book.completed ? 'done' : progress > 0 ? 'reading' : 'available',
    currentText: book.completed ? 'Completed!' : progress > 0 ? 'Keep reading' : 'Start reading',
  }
}

function toFrontendCurrentBook(book: BackendCurrentBook): Book {
  const progress = Math.max(0, Math.min(1, book.progress / 100))
  const localBook = localBookFor({
    id: String(book.bookId),
    title: book.title,
    coverColor: '#ffbd54',
    level: 1,
    totalLessons: 4,
    currentLesson: 1,
    progress,
    status: 'reading',
  })
  return {
    id: String(book.bookId),
    title: localBook?.title ?? book.title,
    coverColor: localBook?.coverColor ?? '#ffbd54',
    coverImage: publicCoverImageUrl(book.coverImageUrl) ?? localBook?.coverImage,
    level: localBook?.level ?? 1,
    totalLessons: localBook?.totalLessons ?? 4,
    currentLesson: Math.max(1, Math.min(4, Math.floor(progress * 4) + 1)),
    progress,
    status: progress >= 1 ? 'done' : progress > 0 ? 'reading' : 'available',
    currentText: book.lessonName ?? localBook?.currentText ?? 'Keep reading',
  }
}

// ─── 로컬 목업 레슨 콘텐츠 ───────────────────────────────

export async function fetchLesson(bookId: string, lessonId: string): Promise<Lesson | undefined> {
  return LESSONS.find((l) => l.bookId === bookId && l.id === lessonId)
}

// ─── 로컬 목업 학습 진도 저장 ────────────────────────────

export async function postProgress(bookId: string, lessonId: string): Promise<void> {
  void bookId
  void lessonId
}

// ─── 보호자 계정 / 프로필 ────────────────────────────────

export interface ParentAuthData {
  parentAccessToken: string
  refreshToken: string
  isNewParent: boolean
  parent: {
    parentId: number
    nickname?: string | null
    profileCount: number
  }
}

export interface ChildProfile {
  profileId: number
  nickname: string
  age: number
  profileImageUrl: string | null
  profileColor?: string
  passwordEnabled: boolean
  onboardingCompleted: boolean
  difficulty: Difficulty | null
}

export interface ProfileListData {
  profiles: ChildProfile[]
  maxProfiles: number
  profileCount: number
}

export interface ProfileLoginData {
  profileAccessToken: string
  profile: ChildProfile
}

export async function signupParent(username: string, password: string, nickname?: string): Promise<ParentAuthData> {
  if (BASE_URL) {
    const data = await post<ParentAuthData>('/auth/signup', { username, password, nickname })
    saveParentSession(data)
    return data
  }
  const data = {
    parentAccessToken: 'mock-parent-token',
    refreshToken: 'mock-refresh-token',
    isNewParent: true,
    parent: { parentId: 1, nickname, profileCount: mockProfiles().length },
  }
  window.localStorage.setItem(MOCK_PARENT_KEY, JSON.stringify({ username, password, nickname }))
  saveParentSession(data)
  return data
}

export async function loginParent(username: string, password: string): Promise<ParentAuthData> {
  if (BASE_URL) {
    const data = await post<ParentAuthData>('/auth/login', { username, password })
    saveParentSession(data)
    return data
  }
  const parent = JSON.parse(window.localStorage.getItem(MOCK_PARENT_KEY) || 'null')
  if (parent && parent.username !== username) throw new Error('INVALID_LOGIN')
  if (parent && parent.password !== password) throw new Error('INVALID_LOGIN')
  const data = {
    parentAccessToken: 'mock-parent-token',
    refreshToken: 'mock-refresh-token',
    isNewParent: false,
    parent: { parentId: 1, nickname: parent?.nickname ?? '부모님', profileCount: mockProfiles().length },
  }
  saveParentSession(data)
  return data
}

export function startKakaoLogin() {
  if (!KAKAO_CLIENT_ID) {
    throw new Error('KAKAO_CLIENT_ID_MISSING')
  }

  const state = crypto.randomUUID()
  window.sessionStorage.setItem('yeongcha:kakao-oauth-state', state)
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: KAKAO_CLIENT_ID,
    redirect_uri: KAKAO_REDIRECT_URI,
    state,
  })
  window.location.href = `https://kauth.kakao.com/oauth/authorize?${params.toString()}`
}

export async function completeKakaoLogin(code: string, state?: string | null): Promise<ParentAuthData> {
  const savedState = window.sessionStorage.getItem('yeongcha:kakao-oauth-state')
  if (state && savedState && state !== savedState) {
    throw new Error('INVALID_KAKAO_STATE')
  }
  window.sessionStorage.removeItem('yeongcha:kakao-oauth-state')

  const data = await post<ParentAuthData>('/auth/kakao', {
    authorizationCode: code,
    redirectUri: KAKAO_REDIRECT_URI,
  })
  saveParentSession(data)
  return data
}

export async function kakaoLoginMock(): Promise<ParentAuthData> {
  const data = {
    parentAccessToken: 'mock-kakao-parent-token',
    refreshToken: 'mock-kakao-refresh-token',
    isNewParent: false,
    parent: { parentId: 1, nickname: '카카오 보호자', profileCount: mockProfiles().length },
  }
  window.localStorage.setItem(MOCK_PARENT_KEY, JSON.stringify({ username: 'kakao', password: '', nickname: '카카오 보호자' }))
  saveParentSession(data)
  return data
}

export async function fetchProfiles(): Promise<ProfileListData> {
  if (BASE_URL) return get('/profiles', getParentToken())
  const profiles = mockProfiles()
  return { profiles, maxProfiles: 5, profileCount: profiles.length }
}

export async function createProfile(input: {
  nickname: string
  age: number
  profilePassword: string
  profileImageId?: number
  profileColor?: string
}): Promise<ChildProfile> {
  if (BASE_URL) {
    return post('/profiles', input, getParentToken())
  }
  const profiles = mockProfiles()
  const profile: ChildProfile & { profilePassword?: string } = {
    profileId: Date.now(),
    nickname: input.nickname,
    age: input.age,
    profileImageUrl: input.profileImageId ? profileImageUrl(input.profileImageId) : null,
    profileColor: input.profileColor,
    passwordEnabled: true,
    onboardingCompleted: false,
    difficulty: null,
    profilePassword: input.profilePassword,
  }
  saveMockProfiles([...profiles, profile])
  return profile
}

export async function updateProfile(profileId: number, input: Partial<Pick<ChildProfile, 'nickname' | 'age'>> & { profileImageId?: number }): Promise<ChildProfile> {
  if (BASE_URL) return patch(`/profiles/${profileId}`, input, getParentToken())
  const profiles = mockProfiles()
  const next = profiles.map((profile) => (
    profile.profileId === profileId
      ? { ...profile, ...input, profileImageUrl: input.profileImageId ? profileImageUrl(input.profileImageId) : profile.profileImageUrl }
      : profile
  ))
  saveMockProfiles(next)
  return next.find((profile) => profile.profileId === profileId) as ChildProfile
}

export async function updateProfilePassword(profileId: number, newPassword: string): Promise<void> {
  if (BASE_URL) {
    await patch(`/profiles/${profileId}/password`, { newPassword }, getParentToken())
    return
  }
  const profiles = mockProfiles() as Array<ChildProfile & { profilePassword?: string }>
  saveMockProfiles(profiles.map((profile) => (
    profile.profileId === profileId
      ? { ...profile, profilePassword: newPassword, passwordEnabled: true }
      : profile
  )))
}

export async function deleteProfile(profileId: number): Promise<void> {
  if (BASE_URL) {
    await del(`/profiles/${profileId}`, getParentToken())
  } else {
    saveMockProfiles(mockProfiles().filter((profile) => profile.profileId !== profileId))
  }

  const activeProfile = JSON.parse(window.localStorage.getItem('yeongcha:active-profile') || 'null') as ChildProfile | null
  if (activeProfile?.profileId === profileId) {
    clearProfileSession()
  }
}

export function clearProfileSession() {
  window.localStorage.removeItem(PROFILE_TOKEN_KEY)
  window.localStorage.removeItem('yeongcha:active-profile')
}

export async function logoutProfile(): Promise<void> {
  if (BASE_URL && getProfileToken()) {
    try {
      const res = await fetch(`${BASE_URL}/profile-auth/logout`, {
        method: 'POST',
        headers: authHeaders(getProfileToken()),
      })
      if (!res.ok) await handleResponse(res, 'POST', '/profile-auth/logout')
    } finally {
      clearProfileSession()
    }
    return
  }
  clearProfileSession()
}

export async function loginProfile(profileId: number, profilePassword: string): Promise<ProfileLoginData> {
  if (BASE_URL) {
    const data = await post<ProfileLoginData>(`/profiles/${profileId}/login`, { profilePassword }, getParentToken())
    saveProfileSession(data)
    return data
  }
  const profile = mockProfiles().find((item) => item.profileId === profileId) as (ChildProfile & { profilePassword?: string }) | undefined
  if (!profile || profile.profilePassword !== profilePassword) throw new Error('INVALID_PROFILE_PIN')
  const data = { profileAccessToken: `mock-profile-token-${profileId}`, profile }
  saveProfileSession(data)
  return data
}

export async function logoutParent(): Promise<void> {
  const refreshToken = window.localStorage.getItem('yeongcha:refresh-token')
  if (BASE_URL && refreshToken) {
    try {
      await post('/auth/logout', { refreshToken })
    } finally {
      clearParentSession()
    }
    return
  }
  clearParentSession()
}

function clearParentSession() {
  window.localStorage.removeItem(PARENT_TOKEN_KEY)
  window.localStorage.removeItem(PROFILE_TOKEN_KEY)
  window.localStorage.removeItem('yeongcha:refresh-token')
  window.localStorage.removeItem('yeongcha:active-profile')
  window.localStorage.removeItem('yeongcha:onboarding-completed')
  window.localStorage.removeItem('yeongcha:placement-level')
}

// ─── 온보딩 제출  POST /profiles/me/onboarding ───────────

export interface OnboardingAnswer {
  questionId: number
  answer: string
}

export interface OnboardingResult {
  profileId?: number
  onboardingScore: number
  difficulty: Difficulty
  onboardingCompleted: boolean
}

export async function postOnboarding(answers: OnboardingAnswer[]): Promise<OnboardingResult> {
  if (BASE_URL) return post('/profiles/me/onboarding', { answers }, getProfileToken())
  const normalized = Object.fromEntries(answers.map((answer) => [answer.questionId, answer.answer.toLowerCase()]))
  const onboardingScore = normalized[3] !== 'apple' ? 2 : normalized[4] === 'rain' ? 14 : 8
  const result: OnboardingResult = {
    onboardingScore,
    difficulty: onboardingScore <= 6 ? 'BEGINNER' : onboardingScore <= 12 ? 'INTERMEDIATE' : 'ADVANCED',
    onboardingCompleted: true,
  }
  window.localStorage.setItem(ONBOARDING_RESULT_KEY, JSON.stringify(result))
  const activeProfile = JSON.parse(window.localStorage.getItem('yeongcha:active-profile') || 'null') as ChildProfile | null
  if (activeProfile) {
    saveMockProfiles(mockProfiles().map((profile) => (
      profile.profileId === activeProfile.profileId
        ? { ...profile, onboardingCompleted: true, difficulty: result.difficulty }
        : profile
    )))
  }
  return result
}

// ─── 음성 인식  POST /speech/recognize ──────────────────

export interface SpeechResult {
  recognized: string
  correct: boolean
  score: number
}

export async function postSpeechRecognize(audio: Blob, expected: string): Promise<SpeechResult> {
  void audio
  await new Promise((resolve) => setTimeout(resolve, 1500))
  return { recognized: expected, correct: true, score: 1.0 }
}

// ─── 학습 세션 API  /learning-sessions ───────────────────

export type CourseType = 'READING' | 'REPEAT' | 'DESCRIPTION' | 'ROLEPLAY'

export function usesBackendApi(): boolean {
  return Boolean(BASE_URL && getProfileToken())
}

export interface LearningSessionData {
  sessionId: number
  bookId: number
  isNew?: boolean
  status: 'IN_PROGRESS' | 'EXITED' | 'COMPLETED'
  currentCourse: CourseType
  currentCourseNumber: number
  currentStep: number
  totalProgress: number
}

export interface ReadingData {
  courseType: 'READING'
  courseNumber: number
  currentStep: number
  totalSteps: number
  courseProgress: number
  totalProgress: number
  content: {
    chunkId: number
    text: string
    imageUrl?: string | null
  }
}

export interface ReadingProgressData {
  currentStep?: number
  totalSteps?: number
  courseProgress: number
  totalProgress: number
  courseCompleted: boolean
  nextCourse?: CourseType
  content?: ReadingData['content']
}

export interface RepeatData {
  courseType: 'REPEAT'
  courseNumber: number
  currentStep: number
  totalSteps: number
  courseProgress: number
  totalProgress: number
  content: {
    questionId: number
    targetText: string
    imageUrl?: string | null
  }
}

export interface AttemptData {
  attemptId: number
  questionId: number
  targetText?: string
  transcript: string
  score: number
  passed: boolean
  feedback?: string
  modelAnswer?: string | null
  guideHint?: string | null
  courseProgress: number
  totalProgress: number
}

export interface QuestionProgressData {
  currentStep?: number
  totalSteps?: number
  courseProgress: number
  totalProgress: number
  courseCompleted: boolean
  nextCourse?: CourseType
}

export interface DescriptionData {
  courseType: 'DESCRIPTION'
  courseNumber: number
  currentStep: number
  totalSteps: number
  courseProgress: number
  totalProgress: number
  content: {
    questionId: number
    questionType: 'WORD_GUESS' | 'FILL_BLANK' | 'DESCRIPTION' | 'WHY_QUESTION'
    instruction: string
    imageUrl?: string | null
    sentence?: string | null
    pageNumber?: number | null
    sourceText?: string | null
    blankWord?: string | null
    answerSentence?: string | null
    guideHint?: string | null
  }
}

export interface RoleplayData {
  courseType: 'ROLEPLAY'
  courseNumber: number
  courseProgress: number
  totalProgress: number
  mission: {
    missionId: number
    title: string
    description: string
    playerGoal?: string | null
    hints?: string[]
    requiredTurns?: number
  }
  character: {
    name: string
    imageUrl?: string | null
  }
  openingMessage: {
    speaker: string
    text: string
  }
}

export interface RoleplayMessageData {
  messageId: number
  turn: number
  user: {
    transcript: string
  }
  character: {
    speaker: string
    text: string
  }
  score: number
  missionCompleted: boolean
  courseProgress: number
  totalProgress: number
}

export interface CompletionData {
  sessionId: number
  status: 'COMPLETED'
  bookId: number
  totalScore: number
  stars: number
  completedAt: string
  rewards: unknown
}

async function postForm<T>(path: string, form: FormData, token?: string | null): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: authHeaders(token),
    body: form,
  })
  return handleResponse(res, 'POST', path)
}

export async function startOrResumeLearningSession(bookId: string): Promise<LearningSessionData> {
  return post<LearningSessionData>(`/books/${bookId}/sessions`, {}, getProfileToken())
}

export async function fetchLearningSession(sessionId: number): Promise<LearningSessionData> {
  return get<LearningSessionData>(`/learning-sessions/${sessionId}`, getProfileToken())
}

export async function fetchReadingCourse(sessionId: number): Promise<ReadingData> {
  return get<ReadingData>(`/learning-sessions/${sessionId}/reading`, getProfileToken())
}

export async function updateReadingCourse(sessionId: number, currentStep: number): Promise<ReadingProgressData> {
  return patch<ReadingProgressData>(
    `/learning-sessions/${sessionId}/reading/progress`,
    { currentStep },
    getProfileToken(),
  )
}

export async function fetchRepeatCourse(sessionId: number): Promise<RepeatData> {
  return get<RepeatData>(`/learning-sessions/${sessionId}/repeat`, getProfileToken())
}

export async function createRepeatAttempt(sessionId: number, questionId: number, audio: Blob): Promise<AttemptData> {
  const form = new FormData()
  form.append('audio', audio, 'recording.webm')
  form.append('questionId', String(questionId))
  return postForm<AttemptData>(`/learning-sessions/${sessionId}/repeat/attempts`, form, getProfileToken())
}

export async function updateRepeatCourse(sessionId: number, questionId: number): Promise<QuestionProgressData> {
  return patch<QuestionProgressData>(
    `/learning-sessions/${sessionId}/repeat/progress`,
    { questionId },
    getProfileToken(),
  )
}

export async function fetchDescriptionCourse(sessionId: number): Promise<DescriptionData> {
  return get<DescriptionData>(`/learning-sessions/${sessionId}/description`, getProfileToken())
}

export async function createDescriptionAttempt(sessionId: number, questionId: number, audio: Blob): Promise<AttemptData> {
  const form = new FormData()
  form.append('audio', audio, 'recording.webm')
  form.append('questionId', String(questionId))
  return postForm<AttemptData>(`/learning-sessions/${sessionId}/description/attempts`, form, getProfileToken())
}

export async function updateDescriptionCourse(sessionId: number, questionId: number): Promise<QuestionProgressData> {
  return patch<QuestionProgressData>(
    `/learning-sessions/${sessionId}/description/progress`,
    { questionId },
    getProfileToken(),
  )
}

export async function fetchRoleplayCourse(sessionId: number): Promise<RoleplayData> {
  return get<RoleplayData>(`/learning-sessions/${sessionId}/roleplay`, getProfileToken())
}

export async function createRoleplayMessage(sessionId: number, missionId: number, audio: Blob): Promise<RoleplayMessageData> {
  const form = new FormData()
  form.append('audio', audio, 'recording.webm')
  form.append('missionId', String(missionId))
  return postForm<RoleplayMessageData>(`/learning-sessions/${sessionId}/roleplay/messages`, form, getProfileToken())
}

export async function completeLearningSession(sessionId: number): Promise<CompletionData> {
  return post<CompletionData>(`/learning-sessions/${sessionId}/complete`, {}, getProfileToken())
}
