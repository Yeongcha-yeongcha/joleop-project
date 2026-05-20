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

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`)
  return res.json()
}

// ─── 사용자 통계  GET /users/me/stats ───────────────────

export async function fetchUserStats(): Promise<UserStats> {
  if (BASE_URL) return get('/users/me/stats')
  return { streak: 15, hearts: 210, xpPercent: 0.7 }
}

// ─── 책 목록  GET /books ────────────────────────────────

export async function fetchBooks(): Promise<Book[]> {
  if (BASE_URL) return get('/books')
  return BOOKS
}

// ─── 레슨 콘텐츠  GET /books/:bookId/lessons/:lessonId ──

export async function fetchLesson(bookId: string, lessonId: string): Promise<Lesson | undefined> {
  if (BASE_URL) return get(`/books/${bookId}/lessons/${lessonId}`)
  return LESSONS.find((l) => l.bookId === bookId && l.id === lessonId)
}

// ─── 학습 진도 저장  POST /users/me/progress ────────────

export async function postProgress(bookId: string, lessonId: string): Promise<void> {
  if (BASE_URL) {
    await post('/users/me/progress', { bookId, lessonId, completedAt: new Date().toISOString() })
  }
}

// ─── 음성 인식  POST /speech/recognize ──────────────────

export interface SpeechResult {
  recognized: string
  correct: boolean
  score: number
}

export async function postSpeechRecognize(audio: Blob, expected: string): Promise<SpeechResult> {
  if (BASE_URL) {
    const form = new FormData()
    form.append('audio', audio, 'recording.webm')
    form.append('expected', expected)
    const res = await fetch(`${BASE_URL}/speech/recognize`, { method: 'POST', body: form })
    return res.json()
  }
  return { recognized: expected, correct: true, score: 1.0 }
}
