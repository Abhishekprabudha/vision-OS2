# AIonOS — AI Native Vision Agents Film

A GitHub-ready repository that weaves the supplied manufacturing, logistics, port and airport video assets into one narrated cross-industry film. The visual story follows a single operating arc:

**Observe → Understand → Decide → Act**

The final runtime is automatically held below three minutes. The repository includes a browser preview, source clips, scene manifest, narration, captions, FFmpeg renderer and a GitHub Actions workflow that generates a neural-voice MP4.

## What is included

- `dist/ai-native-vision-agents.mp4` — immediately playable preview.
- `index.html` — GitHub Pages showcase with chapters and captions.
- `data/scenes.json` — editable storyline, timings, overlays and source mapping.
- `assets/audio/narration.txt` — the complete narration script.
- `scripts/generate_narration.py` — Microsoft Edge neural TTS with offline eSpeak fallback.
- `scripts/render_video.py` — crop, colour grade, detection overlays, animated scan line, transitions, audio mix, captions and final compression.
- `.github/workflows/render-video.yml` — one-click cloud render.

## Upload through the GitHub website

1. Download and extract the repository ZIP.
2. Create a new empty repository on GitHub.
3. Choose **Add file → Upload files** and drag the extracted repository contents into the upload area, preserving the folders.
4. Commit the upload to `main`.
5. Open **Actions → Render AI Native Vision Agents video → Run workflow**.
6. Keep the default neural voice, or select another Microsoft Edge voice, then run the workflow.
7. When the workflow finishes, download the `AIonOS-AI-Native-Vision-Agents-Film` artifact.

Every individual file is below 25 MB so the repository can be uploaded using the browser rather than Git or Git LFS.

## Publish the preview on GitHub Pages

1. Go to **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select `main` and `/root`, then save.
4. Open the generated Pages URL.

The included preview uses an offline synthetic voice. The GitHub Actions render replaces it with the selected Microsoft Edge neural narration.

## Render locally

Requirements: Python 3.11+, FFmpeg, a DejaVu or Liberation Sans font, and eSpeak for the offline fallback.

```bash
pip install -r requirements.txt
python scripts/validate_repo.py
python scripts/generate_narration.py --engine espeak --output assets/audio/narration.mp3
python scripts/render_video.py --narration assets/audio/narration.mp3
python -m http.server 8000
```

Open `http://localhost:8000`.

## Edit the film

Change `data/scenes.json` to adjust scene order, source clips, trim points, on-screen copy, colours and AI detection boxes. Change `assets/audio/narration.txt` to revise the voiceover. The renderer measures the generated narration and scales the scene timings while enforcing a maximum final duration of 177 seconds.

## Asset provenance

Only media from the supplied repositories was used:

- Airport-Agent-Demo-2-main
- NX-Use-Cases-main
- Port_Tech-main
- Maruti-Safety-intelligence-main

No external footage was added. The repository preserves visible source watermarks where present. Confirm that the supplied assets are cleared for the intended client and public distribution before publishing.
