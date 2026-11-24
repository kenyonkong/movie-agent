import { useEffect, useState } from "react";
import type { KeyboardEvent } from "react";
import { searchMoviesByTitle } from "@/lib/api";
import type { MovieSearchItem } from "@/types/movie";

export function MovieTitleInput({
  query,
  onChange,
  onSelect,
  searching,
}: {
  query: string;
  onChange: (query: string) => void;
  onSelect: (movie: MovieSearchItem) => void;
  searching: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [composing, setComposing] = useState(false);
  const [suggestions, setSuggestions] = useState<MovieSearchItem[]>([]);
  const [activeIndex, setActiveIndex] = useState(-1);
  const title = query.trim();
  const eligible = open && !searching && !composing && title.length >= 2;
  const expanded = eligible && suggestions.length > 0;
  const activeOption = expanded ? suggestions[activeIndex] : undefined;

  useEffect(() => {
    if (!eligible) return;

    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      try {
        const response = await searchMoviesByTitle(title, 6, 0, controller.signal);
        if (!controller.signal.aborted) setSuggestions(response.results);
      } catch {
        if (!controller.signal.aborted) setSuggestions([]);
      }
    }, 250);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [eligible, title]);

  function close() {
    setOpen(false);
    setActiveIndex(-1);
    setSuggestions([]);
  }

  function select(movie: MovieSearchItem) {
    close();
    onSelect(movie);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.nativeEvent.isComposing || composing) return;

    if (event.key === "Escape" && open) {
      event.preventDefault();
      close();
    } else if (event.key === "Enter" && activeOption) {
      event.preventDefault();
      select(activeOption);
    } else if (event.key === "Enter") {
      close();
    } else if (expanded && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
      event.preventDefault();
      setActiveIndex((index) => {
        if (event.key === "ArrowDown") return (index + 1) % suggestions.length;
        return index <= 0 ? suggestions.length - 1 : index - 1;
      });
    }
  }

  return (
    <div className="relative min-w-0 flex-1">
      <input
        id="movie-title-search"
        type="text"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={expanded}
        aria-controls={expanded ? "movie-title-options" : undefined}
        aria-activedescendant={activeOption ? `movie-option-${activeIndex}` : undefined}
        value={query}
        maxLength={200}
        onFocus={() => setOpen(true)}
        onBlur={close}
        onKeyDown={handleKeyDown}
        onCompositionStart={() => setComposing(true)}
        onCompositionEnd={() => setComposing(false)}
        onChange={(event) => {
          if (event.target.value.trim() !== title) setSuggestions([]);
          setActiveIndex(-1);
          setOpen(true);
          onChange(event.target.value);
        }}
        placeholder="Try Batman, Parasite, or Spirited Away"
        autoComplete="off"
        className="warm-field w-full rounded-xl px-4 py-3 outline-none transition"
      />
      {expanded && (
        <ul
          id="movie-title-options"
          role="listbox"
          aria-label="Matching movie titles"
          className="absolute inset-x-0 top-full z-20 mt-2 rounded-xl border border-[#BDB76B] bg-[#FFFDF0] p-1 shadow-lg"
        >
          {suggestions.map((movie, index) => (
            <li
              key={movie.movie_id}
              id={`movie-option-${index}`}
              role="option"
              aria-selected={index === activeIndex}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => select(movie)}
              className={`flex cursor-pointer items-baseline justify-between gap-3 rounded-lg px-3 py-2 text-[#352D22] hover:bg-[#BDB76B]/25 ${index === activeIndex ? "bg-[#BDB76B]/25" : ""}`}
            >
              <span>{movie.title}</span>
              {movie.release_year && (
                <span className="shrink-0 text-sm text-[#706453]">{movie.release_year}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
