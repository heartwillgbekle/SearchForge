"use client";

import { FormEvent } from "react";

interface SearchBarProps {
  query: string;
  onQueryChange: (value: string) => void;
  onSearch: () => void;
  loading: boolean;
}

export default function SearchBar({
  query,
  onQueryChange,
  onSearch,
  loading,
}: SearchBarProps) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSearch();
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
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
  );
}
