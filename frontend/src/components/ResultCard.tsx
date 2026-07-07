import { SearchResult } from "@/lib/api";

export default function ResultCard({ result }: { result: SearchResult }) {
  return (
    <div className="border-t border-gray-200 py-4 dark:border-gray-800">
      <div className="flex items-baseline justify-between gap-4">
        <h3 className="font-mono font-semibold">{result.document}</h3>
        <span className="shrink-0 text-sm text-gray-500">
          Score: {result.score.toFixed(2)}
        </span>
      </div>
      <p className="mt-1 text-gray-600 dark:text-gray-400">{result.snippet}</p>
    </div>
  );
}
