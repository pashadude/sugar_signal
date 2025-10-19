from language_normalization import LanguageNormalizationPipeline

def run_tests():
    pipeline = LanguageNormalizationPipeline()

    test_cases = [
        # Multilingual
        "Hola amigo! ¿Cómo estás?",  # Spanish
        "你好，世界！",                # Chinese
        "مرحبا كيف الحال؟",           # Arabic
        # Slang and informal
        "u r gr8! lol, wassup?",
        "brb, gotta go 2 the store rn",
        # Typo-rich
        "Ths is a smple txt with sme typos.",
        "I relly lik this prodct!!!",
        # Transliterated
        "namaste! ap kaise ho?",  # Hindi greeting in Latin script
        "gr8 job, bhai!",         # Mixed English/Hindi slang
        # Mixed-language (code-switching)
        "Let's go to the mercado for some comida.",
        "今日はgood dayですね。",
        # Edge cases
        "U r the best!!! 😂😂",
        "lol... that's sooo funny!!!",
        "Template: {{user}} is gr8.",
        "Abbr. ambiguity: Dr. Smith met Mr. Jones at 5pm.",
        "I can't believe u did that, smh.",
        "This is 'quoted' and “double quoted” text.",
        "Multiple     spaces     here.",
        "gr8, namaste, lol, u r awesome!",
    ]

    for i, text in enumerate(test_cases, 1):
        normalized = pipeline.normalize(text)
        print(f"Test {i}:")
        print(f"  Original:   {text}")
        print(f"  Normalized: {normalized}")
        print("-" * 60)

    # --- New: Structured sugar pricing normalization tests ---
    structured_cases = [
        [
            "| Contract | Date       | Price  | Volume |",
            "|----------|------------|--------|--------|",
            "| NY11     | 2025-10-19 | 27.50  | 12000  |",
            "| Copper   | 2025-10-19 | 8.50   | 5000   |"
        ],
        [
            "- NY11 sugar: 27.50 (2025-10-19)",
            "- Copper: 8.50 (2025-10-19)"
        ],
        [
            "1. NY11 sugar contract: 27.50 USD, volume 12000",
            "2. Brent oil: 90.00 USD"
        ],
        [
            "NY11: 27.50, Date: 2025-10-19, Volume: 12000",
            "LSU: 28.10, Date: 2025-10-19, Volume: 8000"
        ]
    ]
    for j, lines in enumerate(structured_cases, 1):
        normalized_struct = pipeline.normalize(sugar_pricing_lines=lines)
        print(f"Structured Test {j}:")
        for entry in normalized_struct:
            print(entry)
        print("-" * 60)

if __name__ == "__main__":
    run_tests()