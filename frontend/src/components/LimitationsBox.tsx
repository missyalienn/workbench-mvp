interface LimitationsBoxProps {
  limitations: string[];
}

export function LimitationsBox({ limitations }: LimitationsBoxProps) {
  if (limitations.length === 0) {
    return null;
  }

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
      <h3 className="font-semibold text-amber-800 mb-2">Limitations</h3>
      <ul className="list-disc list-inside text-sm text-amber-700">
        {limitations.map((limitation, idx) => (
          <li key={idx}>{limitation}</li>
        ))}
      </ul>
    </div>
  );
}
