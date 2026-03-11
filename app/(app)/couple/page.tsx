import { createClient } from "@/lib/supabase/server";
import CoupleConnect from "@/components/CoupleConnect";

export default async function CouplePage() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();

  // Check existing couple status
  const { data: couple } = await supabase
    .from("couples")
    .select("id")
    .or(`partner_a_id.eq.${user!.id},partner_b_id.eq.${user!.id}`)
    .maybeSingle();

  // Check for existing pending invite the user created
  const { data: existingInvite } = await supabase
    .from("couple_invites")
    .select("invite_code, expires_at")
    .eq("inviter_id", user!.id)
    .eq("accepted", false)
    .maybeSingle();

  return (
    <div className="flex flex-col h-[calc(100dvh-64px)]">
      <div className="px-5 pt-12 pb-4 border-b border-sand-100 bg-sand-50">
        <h1 className="text-xl font-semibold text-stone-800">Connect</h1>
        <p className="text-sm text-stone-400 mt-0.5">Link with your partner</p>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-6">
        <CoupleConnect
          userId={user!.id}
          alreadyConnected={!!couple}
          existingInviteCode={existingInvite?.invite_code ?? null}
        />
      </div>
    </div>
  );
}
