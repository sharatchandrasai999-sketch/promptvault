"""Command-line interface for promptvault.

Usage:
    promptvault [--store DIR] save --name NAME --text "PROMPT"
    promptvault [--store DIR] list [--name NAME]
    promptvault [--store DIR] ab --name NAME --v1 1 --v2 2 --testset FILE.json

The store defaults to ~/.promptvault; override it with --store or the
PROMPTVAULT_STORE environment variable. Exit code 0 on success, 2 on a
user-facing error (missing prompt, missing version, bad test set).
"""

from __future__ import annotations

import argparse
import sys

from .ab import run_ab
from .store import (
    PromptVaultError,
    list_prompts,
    list_versions,
    resolve_store,
    save_prompt,
)


def _add_store(parser: argparse.ArgumentParser, *, suppress_default: bool = False) -> None:
    # Subparsers use SUPPRESS so a --store given before the subcommand
    # is not clobbered by the subparser's own default.
    parser.add_argument(
        "--store",
        default=argparse.SUPPRESS if suppress_default else None,
        help="store directory (default ~/.promptvault, or $PROMPTVAULT_STORE)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptvault",
        description="Version prompts on disk and A/B test them with a mock LLM.",
    )
    _add_store(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    p_save = sub.add_parser("save", help="save a new version of a prompt")
    p_save.add_argument("--name", required=True, help="prompt name")
    p_save.add_argument("--text", required=True, help="prompt text")
    _add_store(p_save, suppress_default=True)

    p_list = sub.add_parser("list", help="list saved prompts or one prompt's versions")
    p_list.add_argument("--name", default=None, help="show versions of one prompt")
    _add_store(p_list, suppress_default=True)

    p_ab = sub.add_parser("ab", help="A/B test two versions over a test set")
    p_ab.add_argument("--name", required=True, help="prompt name")
    p_ab.add_argument("--v1", type=int, required=True, help="first version number")
    p_ab.add_argument("--v2", type=int, required=True, help="second version number")
    p_ab.add_argument("--testset", required=True, help="JSON test set file")
    _add_store(p_ab, suppress_default=True)

    return parser


def _store_from(args: argparse.Namespace) -> "object":
    # A --store given after the subcommand wins over one given before it.
    return resolve_store(getattr(args, "store", None))


def _cmd_save(args) -> int:
    store = _store_from(args)
    version = save_prompt(store, args.name, args.text)
    print(f"Saved {args.name!r} version {version}")
    return 0


def _cmd_list(args) -> int:
    store = _store_from(args)
    if args.name:
        versions = list_versions(store, args.name)
        print(f"{args.name}: {len(versions)} version(s)")
        for entry in versions:
            preview = entry["text"].replace("\n", " ")[:60]
            print(f"  v{entry['version']} [{entry['created']}] {preview}")
    else:
        prompts = list_prompts(store)
        if not prompts:
            print("No prompts saved yet.")
            return 0
        for name, count in prompts:
            print(f"{name}: {count} version(s)")
    return 0


def _cmd_ab(args) -> int:
    store = _store_from(args)
    result = run_ab(store, args.name, args.v1, args.v2, args.testset)
    for key in ("v1", "v2"):
        row = result[key]
        print(
            f"v{row['version']}: accuracy {row['accuracy']:.0%} "
            f"({int(row['accuracy'] * result['cases'])}/{result['cases']}), "
            f"mean latency {row['mean_latency_ms']:.3f} ms"
        )
    print(f"Winner: v{result['winner']} (higher accuracy, tie-break: lower latency)")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "save":
            return _cmd_save(args)
        if args.command == "list":
            return _cmd_list(args)
        if args.command == "ab":
            return _cmd_ab(args)
    except PromptVaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
