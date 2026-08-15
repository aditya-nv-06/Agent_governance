import { useState } from "react";

export default function AuthPage({ onAuthenticate, error }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await onAuthenticate(mode, { email, password });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-black px-5 py-8 text-white sm:px-8">
      <div className="mx-auto grid min-h-[80vh] max-w-5xl items-center gap-12 lg:grid-cols-[1.2fr_0.8fr]">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-emerald-200">Governance control plane</p>
          <h1 className="mt-4 text-5xl font-medium tracking-tight sm:text-6xl">Control every agent action.</h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-white/60">An admin-only workspace for defining agent policy, reviewing exceptions, and keeping an auditable record of every decision.</p>
          <div className="mt-10 grid gap-3 text-sm text-white/60 sm:grid-cols-3">
            <p className="border border-white/15 p-4"><span className="block text-white">Define</span>Profile tools, data, and actions.</p>
            <p className="border border-white/15 p-4"><span className="block text-white">Review</span>Approve only policy exceptions.</p>
            <p className="border border-white/15 p-4"><span className="block text-white">Audit</span>Keep every decision traceable.</p>
          </div>
        </div>

        <form onSubmit={submit} className="border border-white/20 bg-white/[0.03] p-7 sm:p-8">
          <div className="flex gap-5 border-b border-white/15 pb-4 text-sm">
            {[["login", "Sign in"], ["register", "Create admin"]].map(([value, label]) => (
              <button type="button" key={value} onClick={() => setMode(value)} className={mode === value ? "text-white" : "text-white/45 hover:text-white"}>{label}</button>
            ))}
          </div>
          <h2 className="mt-6 text-2xl font-medium">{mode === "login" ? "Welcome back" : "Create admin access"}</h2>
          <p className="mt-2 text-sm text-white/50">All registered users have the administrator role.</p>
          {error && <p className="mt-5 border border-rose-300/50 bg-rose-300/10 p-3 text-sm text-rose-100">{error}</p>}
          <label className="mt-6 block text-xs text-white/60">Email<input type="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full border border-white/25 bg-black px-3 py-3 text-sm outline-none focus:border-white" placeholder="admin@company.com" /></label>
          <label className="mt-4 block text-xs text-white/60">Password<input type="password" required minLength="8" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full border border-white/25 bg-black px-3 py-3 text-sm outline-none focus:border-white" placeholder="At least 8 characters" /></label>
          <button disabled={submitting} className="mt-6 w-full bg-white px-4 py-3 text-sm font-medium text-black hover:bg-white/80 disabled:opacity-50">{submitting ? "Please wait…" : mode === "login" ? "Sign in" : "Create admin account"}</button>
        </form>
      </div>
    </main>
  );
}
