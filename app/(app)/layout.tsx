import Nav from "@/components/Nav";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) redirect("/");

  return (
    <div className="flex flex-col min-h-screen max-w-lg mx-auto">
      <main className="flex-1 overflow-hidden">{children}</main>
      <Nav />
    </div>
  );
}
