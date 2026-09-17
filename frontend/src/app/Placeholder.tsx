// Frontend implementation hasn't started (see CLAUDE.md) — every route renders this for now.
export function Placeholder({ title, spec }: { title: string; spec: string }) {
  return (
    <section>
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p className="mt-2 text-slate-600">Placeholder — not implemented yet. Spec: {spec}</p>
    </section>
  );
}
