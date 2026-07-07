"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import * as api from "@/lib/api";

interface SearchBarProps {
  query: string;
  onQueryChange: (value: string) => void;
  onSearch: () => void;
  onSelectSuggestion: (value: string) => void;
  loading: boolean;
}

export default function SearchBar({
  query,
  onQueryChange,
  onSearch,
  onSelectSuggestion,
  loading,
}: SearchBarProps) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [open, setOpen] = useState(false);
  // Set right after a suggestion is chosen so we skip the fetch it triggers.
  const skipNextFetch = useRef(false);

  // Debounced autocomplete: wait 250ms after the last keystroke.
  useEffect(() => {
    const trimmed = query.trim();

    if (skipNextFetch.current) {
      skipNextFetch.current = false;
      return;
    }
    if (!trimmed) {
      setSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const res = await api.autocomplete(trimmed);
        setSuggestions(res.suggestions);
        setOpen(res.suggestions.length > 0);
      } catch {
        setSuggestions([]);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setOpen(false);
    onSearch();
  }

  function chooseSuggestion(value: string) {
    skipNextFetch.current = true;
    setOpen(false);
    setSuggestions([]);
    onSelectSuggestion(value);
  }

  return (
    <div className="relative">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          onFocus={() => setOpen(suggestions.length > 0)}
          // Delay so a click on a suggestion registers before closing.
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder="machine learning"
          className="flex-1 rounded-md border border-gray-300 px-4 py-2 text-base outline-none focus:border-gray-500 dark:border-gray-700 dark:bg-gray-900"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="rounded-md bg-gray-900 px-6 py-2 font-medium text-white transition-colors hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-300"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {open && suggestions.length > 0 && (
        <ul className="absolute left-0 right-0 top-full z-10 mt-1 overflow-hidden rounded-md border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-900">
          {suggestions.map((suggestion) => (
            <li key={suggestion}>
              <button
                type="button"
                // onMouseDown fires before input blur, so the click isn't lost.
                onMouseDown={() => chooseSuggestion(suggestion)}
                className="block w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                {suggestion}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
