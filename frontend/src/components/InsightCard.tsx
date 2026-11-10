type Props = {
  insight: string | null;
};

export function InsightCard({ insight }: Props) {
  if (!insight) {
    return <p className="text-sm text-mute">Insight belum tersedia.</p>;
  }

  const paragraphs = insight
    .split(/\n{2,}/)
    .map((part) => part.trim())
    .filter(Boolean);

  return (
    <div className="space-y-4">
      {paragraphs.map((part) => (
        <p key={part.slice(0, 40)} className="text-[15px] leading-7 text-ink/90">
          {part}
        </p>
      ))}
    </div>
  );
}
