import ChatInterface from "@/components/ChatInterface";
import { createClient } from "@/lib/supabase/server";
import Link from "next/link";

export default async function UsPage() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();

  // Check if user is connected to a partner
  const { data: couple } = await supabase
    .from("couples")
    .select("id, partner_a_id, partner_b_id")
    .or(`partner_a_id.eq.${user!.id},partner_b_id.eq.${user!.id}`)
    .maybeSingle();

  if (!couple) {
    return (
      <div className="flex flex-col h-[calc(100dvh-64px)]">
        <div className="px-5 pt-12 pb-4 border-b border-sand-100 bg-sand-50">
          <h1 className="text-xl font-semibold text-stone-800">Our Space</h1>
          <p className="text-sm text-stone-400 mt-0.5">A shared space for both of you</p>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center px-8 text-center">
          <div className="w-16 h-16 rounded-full bg-sand-100 flex items-center justify-center mb-6">
            <svg viewBox="0 0 24 24" className="w-8 h-8 fill-sand-400" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-stone-700 mb-2">Connect with your partner</h2>
          <p className="text-sm text-stone-400 leading-relaxed mb-8">
            Our Space opens once you and your partner connect. Head to Connect to invite them.
          </p>
          <Link
            href="/couple"
            className="bg-sand-600 text-white px-6 py-3 rounded-2xl text-sm font-medium transition active:scale-95"
          >
            Connect with partner →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100dvh-64px)]">
      <div className="px-5 pt-12 pb-4 border-b border-sand-100 bg-sand-50">
        <h1 className="text-xl font-semibold text-stone-800">Our Space</h1>
        <p className="text-sm text-stone-400 mt-0.5">Your relationship counselor holds this space</p>
      </div>

      <div className="flex-1 overflow-hidden">
        <ChatInterface
          agentMode="relationship"
          userId={user!.id}
          placeholder="What would you like to explore together…"
        />
      </div>
    </div>
  );
}
