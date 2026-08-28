# ElevenLabs options

## Voice and model selection

Obtain the voice ID from the user's ElevenLabs account, an existing project configuration, or the current ElevenLabs voice listing. Do not guess a private or cloned voice ID.

Common public examples previously used by this repository include:

- `JBFqnCBsd6RMkjVDRZzb` — George
- `EXAVITQu4vr4xnSDxMaL` — Sarah
- `onwK4e9ZLuTAKqWW03F9` — Daniel

`eleven_multilingual_v2` is a sensible model example for multilingual narration. Confirm current account availability when model choice matters. Keep changing service identifiers here rather than expanding the discovery description.

## Generator arguments

```text
--text TEXT                 Short literal narration
--text-file PATH            UTF-8 narration file
--output PATH               Required .mp3 destination
--voice-id ID               Required unless ELEVENLABS_VOICE_ID is set
--model-id ID               Defaults to eleven_multilingual_v2
--stability 0..1            Defaults to a neutral 0.5 narration baseline
--similarity-boost 0..1      Defaults to moderately strong matching at 0.75
--approve-paid-use          Required for non-local API endpoints
--force                     Permit overwriting the destination
--timeout SECONDS           Overall request timeout; default 120
--base-url URL              Override endpoint for a local test server
--json                      Emit a machine-readable success result
--play                      Attempt playback after successful generation
```

Use exactly one of `--text` and `--text-file`. The API key is read only from `ELEVENLABS_API_KEY`, never a command-line argument.

## Local evaluation

`--base-url` accepts a loopback mock server such as `http://127.0.0.1:8080`. The paid-use flag is not required for loopback endpoints, allowing request and error handling to be tested without contacting ElevenLabs.

The mock response must return an `audio/*` content type and bytes beginning with an MP3 signature. Never point an evaluation at a remote endpoint without explicit approval.
