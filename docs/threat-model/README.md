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

- t4 (High): harassment tool. Reduced by guild-only, optional guild and channel allowlists, `/optout`, no mention parsing and an audit line. Still open: level 11 is unchanged (a policy choice for the maintainer), the opt-out does not cover the free-text `target` or Matrix `!thegame @user`, and the default opt-out list is in memory.

Mitigated by the abuse controls in issue #111 (settings in the main README, "Abuse controls"): t6 (High, cooldown, concurrency cap, batch cap, Matrix auto-join allowlist, bots ignored) and t10 (audit line). Their residual risks are written in each threat.

## UNVERIFIED items

- t18: image signing, SBOM and provenance are implemented in the shared GYST workflows
- t3: exact default content filtering of the Gemini API (no safety settings are set in the code read).
- t8: whether any client library puts a host name, URL or key fragment in an exception message.
- t12: privacy-notice wording in README and BOT_SETUP.md.
- Behavior of hypeman-social was read at tag v0.3.4 from its own repository, not from the installed package.

## Status counts

20 threats: 13 Open, 7 Mitigated

Mitigated means the control was seen in the code; the threat's `mitigation` field cites file and function. Nothing here is a complete audit.
