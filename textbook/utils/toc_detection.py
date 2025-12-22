
import re
from .bayesian_detection import predict, create_binary_likelihood_dict, create_distribution_dict

PRIOR_TOC = 0.5
TOC_DETECTION_THRESHOLD = 0.05

BINARY_LIKELIHOODS = create_binary_likelihood_dict([
    ("has_keyword_contents", 0.90, 0.0001),
    ("has_roman_numerals", 0.65, 0.08),
    ("has_word_index_reference_bibliography_keywords", 0.95, 0.5),
])

NUMERICAL_DISTRIBUTIONS = create_distribution_dict([
    ("number_of_page_numbers", 20, 5),
])


def detect_toc(page_text: str) -> bool:
    has_keyword_contents = "contents" in page_text.lower()
    has_roman_numerals = any(
        re.search(r"\b[ivxlcdm]+\b", line) for line in page_text.split("\n")
    )
    number_of_page_numbers = sum(
        1 for line in page_text.split("\n") if re.search(r"\b\d+\b", line)
    )
    has_word_index_reference_bibliography_keywords = any(
        re.search(r"\b(index|bibliography|references)\b", line) for line in page_text.split("\n")
    )

    features = {
        "binary_features": {
            "has_keyword_contents": has_keyword_contents,
            "has_roman_numerals": has_roman_numerals,
            "has_word_index_reference_bibliography_keywords": has_word_index_reference_bibliography_keywords,
        },
        "numerical_features": {"number_of_page_numbers": number_of_page_numbers},
    }
    return (
        predict(features["binary_features"], features["numerical_features"], PRIOR_TOC, BINARY_LIKELIHOODS, NUMERICAL_DISTRIBUTIONS)
        > TOC_DETECTION_THRESHOLD
    )  # threshold for TOC detection


if __name__ == "__main__":
    test_samples = [
        {
            "binary_features": {
                "has_keyword_contents": True,
                "has_roman_numerals": True,
                "has_word_index_reference_bibliography_keywords": True,
            },
            "numerical_features": {"number_of_page_numbers": 10},
        },
        {
            "binary_features": {
                "has_keyword_contents": False,
                "has_roman_numerals": True,
                "has_word_index_reference_bibliography_keywords": True,
            },
            "numerical_features": {"number_of_page_numbers": 10},
        },
        {
            "binary_features": {
                "has_keyword_contents": True,
                "has_roman_numerals": False,
                "has_word_index_reference_bibliography_keywords": True,
            },
            "numerical_features": {"number_of_page_numbers": 10},
        },
        {
            "binary_features": {
                "has_keyword_contents": False,
                "has_roman_numerals": True,
                "has_word_index_reference_bibliography_keywords": False,
            },
            "numerical_features": {"number_of_page_numbers": 10},
        },
    ]
    for sample in test_samples:
        print(f"Sample: {sample}")
        print(f"Probability of TOC: {predict(sample['binary_features'], sample['numerical_features'], PRIOR_TOC, BINARY_LIKELIHOODS, NUMERICAL_DISTRIBUTIONS)}")
