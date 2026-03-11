import ChatInterface from "@/components/ChatInterface";
import { createClient } from "@/lib/supabase/server";

export default async function ChatPage() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();

  return (
    <div className="flex flex-col h-[calc(100dvh-64px)]">
      {/* Header */}
      <div className="px-5 pt-12 pb-4 border-b border-sand-100 bg-sand-50">
        <h1 className="text-xl font-semibold text-stone-800">My Space</h1>
        <p className="text-sm text-stone-400 mt-0.5">Private — just you and your counselor</p>
      </div>

      {/* Chat */}
      <div className="flex-1 overflow-hidden">
        <ChatInterface
          agentMode="private"
          userId={user!.id}
          placeholder="What's on your mind…"
        />
      </div>
    </div>
  );
}
