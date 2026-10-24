# Threat model

`yomama-as-a-service.threat-dragon.json` is an OWASP Threat Dragon v2 model of this repository, drawn from the code. Open it with the Threat Dragon desktop or web app (File > Open).

## What it covers

The Discord bot, the Matrix bot, the CLI, the joke generator and its prompt, the shared hypeman-social LLM layer (Gemini or Ollama), secrets handling, and the image build and release pipeline. There is no HTTP server in this repository: callers are chat users reaching the bots through Discord and Matrix.

## Trust boundaries

- Internet: chat platforms and users (untrusted) to the bot runtime.
- Bot runtime (container or systemd service) to the LLM backends (Google Gemini, or an Ollama server).
- Bot runtime to the secrets stores (.env, container environment, Doppler/AWS/Vault).
- Build and release pipeline (GitHub Actions calling shared workflows) to the published image.

## Open High or Critical threats

- t4 (High): The bot is an unrestricted harassment tool: any member can aim maximum-cruelty output at a named user
- t6 (High): No rate limit, cooldown or allowlist: any chat user can drain the shared LLM quota and keep the bot busy
- t7 (High): One slow or retrying LLM call freezes the whole bot (blocking calls inside the event loop)

## UNVERIFIED items

- t18: image signing, SBOM and provenance are implemented in the shared GYST workflows
- t3: exact default content filtering of the Gemini API (no safety settings are set in the code read).
- t8: whether any client library puts a host name, URL or key fragment in an exception message.
- t12: privacy-notice wording in README and BOT_SETUP.md.
- Behavior of hypeman-social was read at tag v0.3.4 from its own repository, not from the installed package.

## Status counts

20 threats: 16 Open, 4 Mitigated

Mitigated means the control was seen in the code; the threat's `mitigation` field cites file and function. Nothing here is a complete audit.
