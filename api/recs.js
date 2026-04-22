import { createClient } from '@supabase/supabase-js'

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY)

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST')

  if (req.method === 'GET') {
    const { status } = req.query
    let q = supabase.from('recommendations').select('*').order('final_score', { ascending: false })
    if (status) q = q.eq('status', status)
    const { data } = await q
    return res.json(data || [])
  }

  if (req.method === 'POST') {
    const { id, status } = req.body
    await supabase.from('recommendations').update({ status }).eq('id', id)
    return res.json({ ok: true })
  }

  res.status(405).end()
}
