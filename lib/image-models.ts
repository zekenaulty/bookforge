export const GOOGLE_IMAGE_MODELS = [
  { id: "gemini-3.1-flash-image", label: "Nano Banana 2", detail: "Best balance of quality and speed" },
  { id: "gemini-3.1-flash-lite-image", label: "Nano Banana 2 Lite", detail: "Fastest and lowest cost" },
  { id: "gemini-3-pro-image", label: "Nano Banana Pro", detail: "Highest creative control" },
  { id: "gemini-2.5-flash-image", label: "Nano Banana (legacy)", detail: "Compatibility option" },
] as const;

export type GoogleImageModel = typeof GOOGLE_IMAGE_MODELS[number]["id"];

export const DEFAULT_GOOGLE_IMAGE_MODEL: GoogleImageModel = "gemini-3.1-flash-image";

export function isGoogleImageModel(value: unknown): value is GoogleImageModel {
  return GOOGLE_IMAGE_MODELS.some((model) => model.id === value);
}
