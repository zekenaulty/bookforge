export function artAttemptObjectKey(input: {
  storyId: string;
  assetId: string;
  renderVersion: string;
  model: string;
  lease: string;
}): string {
  return `stories/${input.storyId}/${input.assetId}/${encodeURIComponent(input.renderVersion)}/${encodeURIComponent(input.model)}/${encodeURIComponent(input.lease)}/image`;
}
