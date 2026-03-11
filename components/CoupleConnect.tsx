"use client";

import { createClient } from "@/lib/supabase/client";
import { useState } from "react";
import { useRouter } from "next/navigation";

interface Props {
  userId: string;
  alreadyConnected: boolean;
  existingInviteCode: string | null;
}

export default function CoupleConnect({ userId, alreadyConnected, existingInviteCode }: Props) {
  const [inviteCode, setInviteCode] = useState(existingInviteCode ?? "");
  const [partnerCode, setPartnerCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const supabase = createClient();

  if (alreadyConnected) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 rounded-full bg-sand-100 flex items-center justify-center mx-auto mb-4">
          <span className="text-2xl">✓</span>
        </div>
        <h2 className="text-lg font-semibold text-stone-700 mb-2">You're connected</h2>
        <p className="text-sm text-stone-400">Head to Our Space to talk with your relationship counselor.</p>
      </div>
    );
  }

  async function createInvite() {
    setLoading(true);
    setError("");
    const code = Math.random().toString(36).substring(2, 10).toUpperCase();

    const { error: err } = await supabase.from("couple_invites").insert({
      inviter_id: userId,
      invite_code: code,
      expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    });

    if (err) {
      setError("Couldn't create invite. Try again.");
    } else {
      setInviteCode(code);
    }
    setLoading(false);
  }

  async function copyCode() {
    await navigator.clipboard.writeText(inviteCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function acceptInvite() {
    if (!partnerCode.trim()) return;
    setLoading(true);
    setError("");

    // Look up invite
    const { data: invite, error: fetchErr } = await supabase
      .from("couple_invites")
      .select("id, inviter_id")
      .eq("invite_code", partnerCode.toUpperCase().trim())
      .eq("accepted", false)
      .gt("expires_at", new Date().toISOString())
      .maybeSingle();

    if (fetchErr || !invite) {
      setError("Code not found or expired. Double-check with your partner.");
      setLoading(false);
      return;
    }

    if (invite.inviter_id === userId) {
      setError("You can't use your own invite code.");
      setLoading(false);
      return;
    }

    // Create couple
    const { error: coupleErr } = await supabase.from("couples").insert({
      partner_a_id: invite.inviter_id,
      partner_b_id: userId,
    });

    if (coupleErr) {
      setError("Something went wrong. Try again.");
      setLoading(false);
      return;
    }

    // Mark invite accepted
    await supabase
      .from("couple_invites")
      .update({ accepted: true })
      .eq("id", invite.id);

    setSuccess("You're connected! 🎉");
    setLoading(false);
    setTimeout(() => router.refresh(), 1500);
  }

  return (
    <div className="space-y-8">
      {/* Step 1: Create invite */}
      <section>
        <h2 className="text-base font-semibold text-stone-700 mb-1">Invite your partner</h2>
        <p className="text-sm text-stone-400 mb-4">
          Create a code and share it with your partner. They'll enter it below.
        </p>

        {!inviteCode ? (
          <button
            onClick={createInvite}
            disabled={loading}
            className="w-full py-4 bg-sand-600 text-white rounded-2xl text-sm font-medium transition active:scale-95 disabled:opacity-50"
          >
            Create invite code
          </button>
        ) : (
          <div className="bg-white border border-sand-200 rounded-2xl p-5 text-center">
            <p className="text-xs text-stone-400 mb-2">Your invite code</p>
            <p className="text-3xl font-semibold tracking-widest text-stone-800 mb-4">{inviteCode}</p>
            <button
              onClick={copyCode}
              className="text-sm text-sand-600 font-medium transition active:scale-95"
            >
              {copied ? "Copied!" : "Copy code"}
            </button>
          </div>
        )}
      </section>

      {/* Divider */}
      <div className="flex items-center gap-4">
        <div className="flex-1 h-px bg-sand-200" />
        <span className="text-xs text-stone-400">or</span>
        <div className="flex-1 h-px bg-sand-200" />
      </div>

      {/* Step 2: Accept invite */}
      <section>
        <h2 className="text-base font-semibold text-stone-700 mb-1">Got a code?</h2>
        <p className="text-sm text-stone-400 mb-4">
          Enter the code your partner sent you.
        </p>

        <input
          value={partnerCode}
          onChange={(e) => setPartnerCode(e.target.value.toUpperCase())}
          placeholder="Enter code…"
          maxLength={8}
          className="w-full border border-sand-200 rounded-2xl px-4 py-4 text-center text-xl font-semibold tracking-widest text-stone-800 bg-white focus:outline-none focus:border-sand-400 transition mb-3"
        />

        {error && <p className="text-sm text-red-500 text-center mb-3">{error}</p>}
        {success && <p className="text-sm text-green-600 text-center mb-3">{success}</p>}

        <button
          onClick={acceptInvite}
          disabled={!partnerCode.trim() || loading}
          className="w-full py-4 bg-stone-800 text-white rounded-2xl text-sm font-medium transition active:scale-95 disabled:opacity-40"
        >
          Connect
        </button>
      </section>
    </div>
  );
}
