# Local neural narration feasibility note

The optional “High-quality local voice” prototype uses `kokoro-js` 1.2.1 with the public `onnx-community/Kokoro-82M-v1.0-ONNX` repository. It performs inference in a dedicated module Web Worker and sends sentence-sized `Float32Array` audio chunks to a small Web Audio playback queue on the main thread. The default remains browser `speechSynthesis`; the neural model is not requested until the device-local flag is enabled.

## Deployment and CSP

- The application and Worker do not set a Content-Security-Policy header. Sites serves the application over HTTPS, which is required for WebGPU and persistent storage.
- The q8 model and voice requests resolve to Hugging Face CDN responses with `Access-Control-Allow-Origin: *`. They can therefore be fetched by the deployed browser origin.
- ONNX Runtime assets are emitted as ordinary application/runtime assets by the build. The 92 MB model weights are fetched by the browser from Hugging Face and are never copied into the Cloudflare Worker or deployment archive.
- If a CSP is added later, it must allow the app's worker source and `connect-src https://huggingface.co https://*.hf.co`; deployed headers should be rechecked before tightening it.

## Execution and responsiveness

- WebGPU is available through `WorkerNavigator.gpu`, and ONNX Runtime documents running WebGPU inference from a dedicated Worker. The prototype attempts q8 WebGPU first and reloads on WASM if adapter acquisition or model initialization fails.
- Sites is not cross-origin isolated, so ONNX Runtime shared-memory WASM threading is disabled. The Worker keeps single-threaded WASM inference off the React/main UI thread; writing requests, navigation, and rendering remain independent.
- `kokoro-js.stream()` yields sentence chunks. Each chunk is transferred, not cloned, into the main-thread playback queue. A job id invalidates stale output after stop, skip, section navigation, or reader unmount.
- Neural failure automatically starts the unchanged device `speechSynthesis` path at the latest approximate character position.

## Storage and download

- Transformers.js uses the browser Cache API for model files, and `kokoro-js` maintains a Cache API entry for the selected voice. Enabling the flag also calls `navigator.storage.persist()` from the user gesture; Chromium may silently grant or deny it. A denied request still leaves a best-effort browser cache.
- q8 model: 92,361,116 bytes (92.36 MB decimal).
- Default `af_heart` voice: 522,240 bytes (0.52 MB).
- ONNX Runtime WebGPU/WASM binary plus lazy Worker JavaScript: roughly 22–25 MB in the current dependency set. Expected first enable is approximately 115–120 MB. Subsequent loads normally use the origin cache.
- The model repository also contains `model_q8f16.onnx` (about 86 MB), but `kokoro-js` 1.2.1 does not expose `q8f16` in its supported dtype API. The prototype therefore uses supported `q8` rather than an untyped implementation detail.

## Browser support decision

- Chrome/Chromium desktop supports WebGPU on eligible Windows, macOS, and ChromeOS hardware. Chrome Android supports it from Chrome 121 on eligible Android 12+ Qualcomm/ARM devices.
- Edge desktop follows Chromium but may still return no adapter because of hardware, driver, policy, or acceleration settings. Edge Android support should not be assumed from the brand/version alone.
- The implementation makes no user-agent assumptions: it requests an adapter in the Worker and falls back to WASM for Chrome or Edge on any unsupported or blocked device.

## Primary references

- [kokoro-js browser usage and streaming](https://github.com/hexgrad/kokoro/blob/main/kokoro.js/README.md)
- [Kokoro ONNX model files](https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/tree/main/onnx)
- [Transformers.js WebGPU guide](https://huggingface.co/docs/transformers.js/guides/webgpu)
- [Transformers.js browser-cache environment](https://huggingface.co/docs/transformers.js/main/api/env)
- [ONNX Runtime Web execution providers and WASM fallback](https://onnxruntime.ai/docs/tutorials/web/)
- [ONNX Runtime Worker and WASM environment guidance](https://onnxruntime.ai/docs/tutorials/web/env-flags-and-session-options.html)
- [Chrome WebGPU platform support](https://developer.chrome.com/docs/web-platform/webgpu/overview)
- [Chrome persistent storage guidance](https://web.dev/articles/persistent-storage)
