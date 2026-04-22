import Anthropic from '@anthropic-ai/sdk'
import { createClient } from '@supabase/supabase-js'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY)

function parseJSON(text) {
  let raw = text.trim()
  if (raw.startsWith('```')) {
    raw = raw.split('```')[1] || raw
    if (raw.startsWith('json')) raw = raw.slice(4)
  }
  return JSON.parse(raw.trim())
}

const PROMPT = (song_name, artist, trending, fp) => `
You are a music coach for Summer Victoria — 125k TikTok followers, known for warm intimate acoustic covers.

Her style fingerprint:
Genres: ${JSON.stringify(fp.genres)}
Emotional tones: ${JSON.stringify(fp.emotional_tones)}
Tempo: ${JSON.stringify(fp.tempo_feel)}
Vocal range: ${fp.vocal_range}
Chorus recognizability avg: ${fp.avg_chorus_recognizability}/10
Nostalgia avg: ${fp.avg_nostalgia_factor}/10
Preferred arrangements: ${fp.preferred_arrangements?.join(', ')}
${fp.summary ? `\nHer identity: ${fp.summary}` : ''}

Evaluate this song:
Song: "${song_name}" by ${artist || 'Unknown'}
Trending heat right now: ${trending}/10

Return ONLY this JSON, no other text:
{
  "style_fit": 0_to_100,
  "tip": "2-3 sentences: why it fits her audience and one specific arrangement or hook approach. Sound like a knowledgeable friend, not a coach."
}
`

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'POST')

  if (req.method !== 'POST') return res.status(405).end()

  const { song_name, artist, trending_score = 7 } = req.body
  if (!song_name) return res.status(400).json({ error: 'song_name required' })

  const { data: fpRow } = await supabase
    .from('fingerprint').select('data').eq('id', 1).single()
  if (!fpRow) return res.status(400).json({ error: 'Build your profile first in the Profile tab.' })

  const msg = await anthropic.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 300,
    messages: [{ role: 'user', content: PROMPT(song_name, artist, trending_score, fpRow.data) }],
  })

  const result = parseJSON(msg.content[0].text)
  const final_score = Math.round(result.style_fit * 0.7 + trending_score * 10 * 0.3)

  const { data: rec } = await supabase.from('recommendations').insert({
    song_name,
    artist: artist || null,
    trending_score,
    style_fit_score: result.style_fit,
    final_score,
    tip_text: result.tip,
    status: 'pending',
  }).select().single()

  res.json(rec)
}
