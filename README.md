# promptvault

Version prompts on disk and A/B test them. Each prompt is stored as JSON
(one file per prompt) in `~/.promptvault` by default, overridable with
`--store` or the `PROMPTVAULT_STORE` environment variable.

## The LLM backend is a deterministic mock

There is no API key, no network call, and no real language model here.
A/B tests run against a small rule-based mock (`src/promptvault/mock.py`):
if the prompt mentions "uppercase" the input is uppercased, "lowercase"
lowercases it, "reverse" reverses it, otherwise the input is returned
unchanged. That is enough for two prompt wordings to produce genuinely
different outputs, so the A/B comparison measures something real about
the wording — but it says nothing about how a real LLM would behave.
Latency is real elapsed time per mock call (measured with
`time.perf_counter`); it is tiny and noisy, and reported as measured.

## Install

```bash
pip install -e .
```

## Usage

```bash
# Save versions of a prompt (version numbers auto-increment)
promptvault save --name greet --text "Reply in uppercase."
promptvault save --name greet --text "Reply normally."

# List prompts and their version counts
promptvault list
promptvault list --name greet

# A/B test two versions over a JSON test set:
# [{"input": "hello", "expected": "HELLO"}, ...]
promptvault ab --name greet --v1 1 --v2 2 --testset testset.json
```

## Example output

```
$ promptvault save --name greet --text "Reply in uppercase."
Saved 'greet' version 1
$ promptvault save --name greet --text "Reply normally."
Saved 'greet' version 2
$ promptvault list
greet: 2 version(s)
$ promptvault ab --name greet --v1 1 --v2 2 --testset testset.json
v1: accuracy 100% (3/3), mean latency 0.002 ms
v2: accuracy 0% (0/3), mean latency 0.001 ms
Winner: v1 (higher accuracy, tie-break: lower latency)
```

## Tests

```bash
python -m pytest
```

## License

MIT — see `LICENSE`.
