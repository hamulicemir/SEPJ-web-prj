from rouge_score import rouge_scorer
from Levenshtein import distance as lev_distance


def calculate_metrics(
    generated_text: str,
    reference_text: str,
    generated_facts: dict,
    reference_facts: dict,
) -> dict:
    """
    Calculates evaluation metrics comparing generated content against a golden truth reference.
    Metrics: ROUGE-L (Style/Structure), Levenshtein (Edit Distance), Fact Completeness (Recall).
    """
    metrics = {}

    # Ensure inputs are strings to avoid crashes
    gen_txt = generated_text or ""
    ref_txt = reference_text or ""

    # ROUGE-L Score (Textual overlap/similarity)
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    scores = scorer.score(ref_txt, gen_txt)
    # F-measure ranges 0.0 to 1.0 -> convert to percentage
    metrics["rouge_score"] = round(scores["rougeL"].fmeasure * 100, 2)

    # Levenshtein Similarity (Edit distance normalized to 0-100)
    max_len = max(len(gen_txt), len(ref_txt))
    if max_len == 0:
        lev_score = 100.0
    else:
        dist = lev_distance(gen_txt, ref_txt)
        lev_score = (1 - (dist / max_len)) * 100
    metrics["levenshtein_similarity"] = round(lev_score, 2)

    # Fact Completeness
    # Helper to normalize list items for loose comparison
    def normalize_set(item_list):
        if not item_list:
            return set()
        return set(str(x).strip().lower() for x in item_list)

    # Compare key metadata fields (e.g., persons, locations)
    # aggregate all facts into one big set for a global completeness score
    gen_set = set()
    ref_set = set()

    keys_to_check = ["meta_persons", "meta_place", "meta_time", "meta_date"]

    for key in keys_to_check:
        # Extract lists from dicts, handle missing keys safely
        ref_val = reference_facts.get(key)
        gen_val = generated_facts.get(key)

        # Handle both list and string inputs (e.g. if single person vs list)
        if isinstance(ref_val, str):
            ref_val = [ref_val]
        if isinstance(gen_val, str):
            gen_val = [gen_val]

        # Add prefixed values to set to distinguish types (e.g. "person:Max" vs "place:Max")
        ref_set.update(f"{key}:{item}" for item in normalize_set(ref_val))
        gen_set.update(f"{key}:{item}" for item in normalize_set(gen_val))

    if len(ref_set) == 0:
        fact_score = 100.0
    else:
        found_facts = ref_set.intersection(gen_set)
        fact_score = (len(found_facts) / len(ref_set)) * 100

    metrics["fact_completeness"] = round(fact_score, 2)

    return metrics
