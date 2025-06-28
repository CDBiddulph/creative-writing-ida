import os
import re
from datasets import load_dataset

# Config
SAVE_DIR = "writing_prompts"

# Create output directory
os.makedirs(SAVE_DIR, exist_ok=True)


def clean_prompt(text):
    # Fix broken contractions first
    text = re.sub(r"\b(\w+)\s+n't\b", r"\1n't", text)  # ca n't -> can't

    # Fix token spacing
    text = re.sub(r"\s([?.!,;:'](?!t))", r"\1", text)
    text = re.sub(r"\b([A-Za-z])\s('ll|'ve|'re|'d|'s|'m)\b", r"\1\2", text)

    # Handle quotes properly
    # `` = opening quote (remove space after)
    text = re.sub(r"``\s*", '"', text)
    # '' = closing quote (remove space before)
    text = re.sub(r"\s*\'\'", '"', text)

    # Also handle smart quotes
    text = text.replace('"', '"').replace('"', '"')

    # Fix any double spaces
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


# Load dataset
dataset = load_dataset("euclaise/writingprompts")

# Process and save each split
for split in ["train", "validation", "test"]:
    split_dataset = dataset[split]
    prompts = split_dataset["prompt"]

    # Clean and normalize
    cleaned_prompts = [clean_prompt(p) for p in prompts]

    # Filter for [WP] prompts only
    wp_prompts = []
    for p in cleaned_prompts:
        match = re.match(r"^\[\s*WP\s*\]\s*", p, re.IGNORECASE)
        if match:
            # Remove the [WP] tag and any following spaces
            wp_prompts.append(p[match.end() :])

    # Remove duplicates
    unique_prompts = list(dict.fromkeys(wp_prompts))

    # Save to file
    filename = os.path.join(SAVE_DIR, f"{split}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        for prompt in unique_prompts:
            f.write(prompt + "\n")

    print(f"Saved {len(unique_prompts)} [WP] prompts to {filename}")
