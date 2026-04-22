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

const PROMPT = (songs) => `
Summer Victoria (@summervictoria_music) has 125k TikTok followers. She posts warm, intimate acoustic covers.

Her best performing songs:
${songs.map(s => `- "${s.song_name}" by ${s.artist}`).join('\n')}

Analyze these and return ONLY this JSON object, no markdown, no text before or after:

{
  "genres": {"genre_name": 0.0},
  "emotional_tones": {"tone": 0.0},
  "tempo_feel": {"slow|mid|uptempo": 0.0},
  "vocal_range": "low|mid|high",
  "avg_chorus_recognizability": 1,
  "avg_nostalgia_factor": 1,
  "preferred_arrangements": ["acoustic guitar"],
  "summary": "2 sentences about her musical identity and audience"
}
`

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST')

  if (req.method === 'GET') {
    const { data, error } = await supabase
      .from('fingerprint').select('data, updated_at').eq('id', 1).single()
    if (error || !data) return res.json({ fingerprint: null })
    return res.json({ fingerprint: data.data, updated_at: data.updated_at })
  }

  if (req.method === 'POST') {
    const { songs } = req.body
    if (!songs?.length) return res.status(400).json({ error: 'songs required' })

    const msg = await anthropic.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 1024,
      messages: [{ role: 'user', content: PROMPT(songs) }],
    })

    const fingerprint = parseJSON(msg.content[0].text)
    await supabase.from('fingerprint').upsert({
      id: 1, data: fingerprint, updated_at: new Date().toISOString(),
    })
    return res.json({ fingerprint })
  }

  res.status(405).end()
}
