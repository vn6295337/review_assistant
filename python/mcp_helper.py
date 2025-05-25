#!/usr/bin/env python3
"""
Master Content Prompt Helper

This script assembles summarized chunks into a unified prompt
for use with AI assistants in a local RAG workflow.
"""

import os
import json
import argparse
import glob
import datetime
from pathlib import Path
from typing import List, Optional

# Default directories (fallbacks if no CLI args)
DEFAULT_SUMMARIES_DIR = Path(__file__).resolve().parent.parent / "outputs/summaries"
DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "outputs/prompts"


def load_template(template_path: Path) -> Optional[str]:
    """Load a prompt template file."""
    try:
        return template_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"⚠ Error loading template: {e}")
        return None


def load_summaries(summaries_dir: Path, verbose: bool = False) -> List[dict]:
    """Load all summary JSON files in a directory."""
    summaries = []
    try:
        summary_files = sorted(summaries_dir.glob("summary_*.json"))
        for file in summary_files:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                summaries.append(data)
                if verbose:
                    print(f"✓ Loaded summary: {file.name}")
    except Exception as e:
        print(f"⚠ Error loading summaries: {e}")
    return summaries


def generate_prompt(template: str, summaries: List[dict], title: Optional[str] = None) -> Optional[str]:
    """Assemble the final prompt from summaries and a template."""
    try:
        summary_texts = [s.get("summary", "") for s in summaries if s.get("summary")]
        if not summary_texts:
            raise ValueError("No summaries contain text")

        joined = "\n\n---\n\n".join(summary_texts)
        title = title or f"Content Analysis {datetime.datetime.now():%Y-%m-%d}"

        return template.replace("{summaries}", joined).replace("{title}", title)
    except Exception as e:
        print(f"⚠ Error generating prompt: {e}")
        return None


def save_prompt(prompt: str, output_dir: Path) -> Optional[Path]:
    """Save prompt to a timestamped .txt file."""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"summary_prompt_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt"
        output_path = output_dir / filename
        output_path.write_text(prompt, encoding='utf-8')
        return output_path
    except Exception as e:
        print(f"⚠ Error saving prompt: {e}")
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a master prompt from summarized chunks")
    parser.add_argument("--summaries-dir", type=Path, default=DEFAULT_SUMMARIES_DIR,
                        help="Directory containing summary files")
    parser.add_argument("--template-file", type=Path, required=True,
                        help="Path to the template file")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_PROMPTS_DIR,
                        help="Directory to save the prompt")
    parser.add_argument("--title", type=str, default=None,
                        help="Optional title to override the default")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    args = parser.parse_args()

    if args.verbose:
        print(f"→ Using summaries from: {args.summaries_dir}")
        print(f"→ Using template: {args.template_file}")
        print(f"→ Output will be saved to: {args.output_dir}")

    template = load_template(args.template_file)
    if not template:
        return 1

    summaries = load_summaries(args.summaries_dir, verbose=args.verbose)
    if not summaries:
        print("❌ No summaries loaded")
        return 1

    prompt = generate_prompt(template, summaries, title=args.title)
    if not prompt:
        print("❌ Failed to generate prompt")
        return 1

    output_file = save_prompt(prompt, args.output_dir)
    if not output_file:
        print("❌ Failed to save prompt")
        return 1

    print(f"✓ Prompt saved: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
