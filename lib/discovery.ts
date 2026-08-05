import type { ArtAsset, AuthorProfile, Story } from "./types.ts";

export type StorySort = "recent" | "title-asc" | "title-desc";
export type AuthorSort = "name-asc" | "name-desc" | "recent";

function normalized(value: string) {
  return value.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase().trim();
}

function newestFirst(left?: string, right?: string) {
  const leftTime = left ? Date.parse(left) : 0;
  const rightTime = right ? Date.parse(right) : 0;
  return (Number.isFinite(rightTime) ? rightTime : 0) - (Number.isFinite(leftTime) ? leftTime : 0);
}

function compareTitles(left: string, right: string) {
  return left.localeCompare(right, undefined, { sensitivity: "base", numeric: true });
}

function matchesSearch(fields: string, query: string) {
  const haystack = normalized(fields);
  return normalized(query).split(/\s+/).filter(Boolean).every((term) => haystack.includes(term));
}

export function uniqueGenres(items: Array<readonly string[] | undefined>) {
  const genresByKey = new Map<string, string>();
  for (const item of items) {
    for (const genre of item || []) {
      const label = genre.trim();
      const key = normalized(label);
      if (key && !genresByKey.has(key)) genresByKey.set(key, label);
    }
  }
  return [...genresByKey.values()].sort(compareTitles);
}

function matchesSelectedGenres(candidateGenres: readonly string[] | undefined, selectedGenres: readonly string[]) {
  if (!selectedGenres.length) return true;
  const candidateKeys = new Set((candidateGenres || []).map(normalized));
  return selectedGenres.some((genre) => candidateKeys.has(normalized(genre)));
}

export function filterAndSortStories(stories: readonly Story[], query: string, selectedGenres: readonly string[], sort: StorySort) {
  return stories
    .filter((story) => matchesSearch(`${story.title} ${story.shortDescription}`, query))
    .filter((story) => matchesSelectedGenres(story.foundation?.genres, selectedGenres))
    .sort((left, right) => {
      if (sort === "title-asc") return compareTitles(left.title, right.title);
      if (sort === "title-desc") return compareTitles(right.title, left.title);
      return newestFirst(left.updatedAt, right.updatedAt) || compareTitles(left.title, right.title);
    });
}

export function filterAndSortAuthors(authors: readonly AuthorProfile[], query: string, selectedGenres: readonly string[], sort: AuthorSort) {
  return authors
    .filter((author) => matchesSearch(`${author.displayName} ${author.shortDescription} ${author.voice}`, query))
    .filter((author) => matchesSelectedGenres(author.selectedGenres, selectedGenres))
    .sort((left, right) => {
      if (sort === "name-desc") return compareTitles(right.displayName, left.displayName);
      if (sort === "recent") return newestFirst(left.updatedAt || left.createdAt, right.updatedAt || right.createdAt) || compareTitles(left.displayName, right.displayName);
      return compareTitles(left.displayName, right.displayName);
    });
}

export function latestCoverAsset(story: Pick<Story, "art">, status?: ArtAsset["status"]): ArtAsset | undefined {
  return story.art
    ?.filter((asset) => asset.type === "cover" && (!status || asset.status === status))
    .sort((left, right) => newestFirst(left.updatedAt || left.createdAt, right.updatedAt || right.createdAt))[0];
}

export function latestReadyCover(story: Pick<Story, "art">): ArtAsset | undefined {
  return latestCoverAsset(story, "Ready");
}
