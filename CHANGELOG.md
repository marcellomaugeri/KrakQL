# Changelog

## [1.0.0] - 2026-03-08

Baseline: fork of [Clairvoyance](https://github.com/nikitastupin/clairvoyance) (Apache 2.0).
First public release of *KrakQL*.

### Added
- LLM-guided multi-agent architecture based on Google ADK:
  - Supervisor routing logic
  - Field Advisor
  - Argument Advisor
- Novelty-based exploration scheduler for target-path selection across types and fields.
- Novelty update controls exposed in CLI:
  - `--reward-factor` (`α`)
  - `--decay-factor` (`β`)
- Updated documentation for architecture and usage.

### Changed
- Core probing workflow adapted from wordlist-based guessing to LLM-guided candidate name generation.
- Exploration strategy now uses novelty-based prioritisation of the next Target Path (type or field).
