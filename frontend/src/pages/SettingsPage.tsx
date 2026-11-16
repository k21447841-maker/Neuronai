import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";

export function SettingsPage() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (data.user) { setEmail(data.user.email || ""); setFullName((data.user.user_metadata?.full_name as string) || ""); }
    });
  }, []);

  async function saveProfile() {
    await supabase.auth.updateUser({ data: { full_name: fullName } });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Account Settings</h1>
      <div className="max-w-lg rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
        <div><label className="mb-1 block text-xs text-[#94A3B8]">Email Address</label><input disabled value={email} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-[#94A3B8]" /></div>
        <div><label className="mb-1 block text-xs text-[#94A3B8]">Display Name</label><input value={fullName} onChange={(e) => setFullName(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white" /></div>
        <button onClick={saveProfile} className="rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white">Save Profile</button>
        {saved && <p className="text-xs text-[#22C55E]">Profile updated.</p>}
      </div>
    </div>
  );
}
