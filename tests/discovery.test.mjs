import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { filterAndSortAuthors, filterAndSortStories, latestCoverAsset, latestReadyCover, uniqueGenres } from "../lib/discovery.ts";

function story(overrides) {
  return {
    id: overrides.id,
    title: overrides.title,
    shortDescription: overrides.shortDescription || "",
    foundation: { genres: overrides.genres || [] },
    updatedAt: overrides.updatedAt || "2026-01-01T00:00:00.000Z",
    art: overrides.art || [],
  };
}

test("story discovery searches title and description and matches any selected genre", () => {
  const stories = [
    story({ id: "1", title: "Échoes of Glass", shortDescription: "A quiet lunar mystery", genres: ["Mystery", "Science fiction"] }),
    story({ id: "2", title: "Briar House", shortDescription: "A family returns home", genres: ["Gothic"] }),
  ];

  assert.deepEqual(filterAndSortStories(stories, "echoes", [], "title-asc").map((item) => item.id), ["1"]);
  assert.deepEqual(filterAndSortStories(stories, "lunar", [], "title-asc").map((item) => item.id), ["1"]);
  assert.deepEqual(filterAndSortStories(stories, "glass lunar", [], "title-asc").map((item) => item.id), ["1"]);
  assert.deepEqual(filterAndSortStories(stories, "", ["Gothic", "Mystery"], "title-asc").map((item) => item.id), ["2", "1"]);
});

test("story and author title sorting is stable and case-insensitive", () => {
  const stories = [
    story({ id: "2", title: "zeta" }),
    story({ id: "1", title: "Alpha" }),
  ];
  assert.deepEqual(filterAndSortStories(stories, "", [], "title-asc").map((item) => item.id), ["1", "2"]);
  assert.deepEqual(filterAndSortStories(stories, "", [], "title-desc").map((item) => item.id), ["2", "1"]);

  const authors = [
    { id: "2", displayName: "Zora", shortDescription: "Dreamlike", voice: "Lyrical", selectedGenres: ["Fantasy"] },
    { id: "1", displayName: "Ari", shortDescription: "Direct", voice: "Dry humor", selectedGenres: ["Mystery"] },
  ];
  assert.deepEqual(filterAndSortAuthors(authors, "dry", [], "name-asc").map((item) => item.id), ["1"]);
  assert.deepEqual(filterAndSortAuthors(authors, "", [], "name-desc").map((item) => item.id), ["2", "1"]);
});

test("genre options are deduplicated and the newest ready cover wins", () => {
  assert.deepEqual(uniqueGenres([["Fantasy", "Mystery"], ["fantasy", " Gothic "]]), ["Fantasy", "Gothic", "Mystery"]);
  const cover = latestReadyCover(story({
    id: "1",
    title: "Cover test",
    art: [
      { id: "failed", type: "cover", status: "Failed", updatedAt: "2026-04-03T00:00:00.000Z" },
      { id: "old", type: "cover", status: "Ready", updatedAt: "2026-04-01T00:00:00.000Z" },
      { id: "new", type: "cover", status: "Ready", updatedAt: "2026-04-02T00:00:00.000Z" },
    ],
  }));
  assert.equal(cover?.id, "new");
  assert.equal(latestCoverAsset(story({
    id: "2",
    title: "Retry test",
    art: [
      { id: "old-ready", type: "cover", status: "Ready", updatedAt: "2026-04-01T00:00:00.000Z" },
      { id: "new-failure", type: "cover", status: "Failed", updatedAt: "2026-04-04T00:00:00.000Z" },
    ],
  }))?.id, "new-failure");
});

test("library and author discovery controls remain accessible and incremental", async () => {
  const [client, styles, route] = await Promise.all([
    readFile(new URL("../app/KotobaApp.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../app/api/app/route.ts", import.meta.url), "utf8"),
  ]);
  assert.match(client, /aria-label="Filter and sort stories"/);
  assert.match(client, /aria-label="Filter and sort authors"/);
  assert.match(client, /aria-label=\{`Filter and sort stories by \$\{author\.displayName\}`\}/);
  assert.match(client, /id="author-story-results"/);
  assert.match(client, /aria-pressed=\{active\}/);
  assert.match(client, /IntersectionObserver/);
  assert.match(client, /Show more \{plural\}/);
  assert.match(client, /Retry cover/);
  assert.match(client, /\/api\/app\?assetId=\$\{encodeURIComponent\(cover\.id\)\}/);
  assert.match(client, /onError=\{\(\) => setFailedCoverId\(cover\.id\)\}/);
  assert.match(client, /function MiniStoryCover/);
  assert.match(client, /initialGallery=\{readerGalleryStoryId === selectedStory\.id\}/);
  assert.match(route, /coverJobResult/);
  assert.match(route, /jobs: coverJobs\.get\(String\(row\.id\)\) \|\| \[\]/);
  assert.match(styles, /\.genre-filter button \{[^}]*min-height: 44px/);
  assert.match(styles, /\.incremental-results button \{ min-height: 44px/);
});
