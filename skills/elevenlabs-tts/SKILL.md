---
name: elevenlabs-tts
description: Generates spoken audio with the ElevenLabs text-to-speech API. Use when converting text, summaries, or narration into an audio file or when the user asks to play generated speech aloud.
compatibility: Requires Python 3, curl 7.76 or newer, network access, and ELEVENLABS_API_KEY. Generation may incur paid ElevenLabs usage and requires explicit approval. Playback depends on the host operating system and installed audio tools.
metadata:
  category: audio-generation
---

# ElevenLabs Text-to-Speech

Generate an MP3 only after the user approves potentially paid ElevenLabs usage for the current task. Never expose the API key or send unapproved text to the service.

## Workflow

1. Confirm the exact text, output path, voice ID, and whether playback is requested.
2. Confirm explicit approval for external, potentially paid generation.
3. Preflight without making a request:

   ```bash
   python3 --version
   curl --version
   test -n "$ELEVENLABS_API_KEY"
   ```

   Stop with a clear explanation if a dependency or key is unavailable. Do not install software or create credentials.
4. Put nontrivial narration in a UTF-8 text file, then run the bundled generator using an absolute skill path:

   ```bash
   python3 <skill-directory>/scripts/elevenlabs_tts.py \
     --text-file narration.txt \
     --output narration.mp3 \
     --voice-id <voice-id> \
     --model-id eleven_multilingual_v2 \
     --approve-paid-use
   ```

   Use `--force` only after confirming that overwriting the target is intended. The script does not retry POST requests because a retry could create a duplicate charge.
5. Verify the script reports a successful audio response and a non-empty MP3 written atomically to the requested path.
6. If playback was requested, run:

   ```bash
   python3 <skill-directory>/scripts/play_audio.py narration.mp3
   ```

   Playback failure does not invalidate a successfully generated file. Report the file path and playback limitation separately.

## Options

Read [references/elevenlabs-options.md](references/elevenlabs-options.md) when selecting a voice, model, output behavior, or local mock endpoint. Treat example IDs as changeable service identifiers, not permanent guarantees.
