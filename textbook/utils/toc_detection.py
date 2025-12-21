# Why use a Bayesian model for seemly trivial TOC detection?
# YES

import re
import math
from typing import Dict
import numpy as np

PRIOR_TOC = 0.5
TOC_DETECTION_THRESHOLD = 0.05

BINARY_LIKELIHOODS = {
    "TOC": {"has_contents_keyword": 0.90, "has_roman_numerals": 0.65, "has_word_index_reference_bibliography_keywords": 0.95, },
    "NOT_TOC": {"has_contents_keyword": 0.0001, "has_roman_numerals": 0.08, "has_word_index_reference_bibliography_keywords": 0.5},
}

# Numerical features (Poisson)
NUMERICAL_DISTRIBUTIONS = {
    "TOC": {
        "number_of_page_numbers": {
            "lambda": 20 # average number of page numbers per page
        }  
    },
    "NOT_TOC": {"number_of_page_numbers": {"lambda": 5}},
}


def poisson_pdf(x: int, lambda_value: float) -> float:
    return (lambda_value**x * math.exp(-lambda_value)) / math.factorial(x)


def predict(
    binary_features: Dict[str, bool], numerical_features: Dict[str, int]
) -> float:
    log_p_toc = np.log(PRIOR_TOC)
    log_p_not_toc = np.log(1 - PRIOR_TOC)

    # Handle binary features
    for feature, observed in binary_features.items():
        if observed:
            log_p_toc += np.log(BINARY_LIKELIHOODS["TOC"][feature])
            log_p_not_toc += np.log(BINARY_LIKELIHOODS["NOT_TOC"][feature])
        else:
            log_p_toc += np.log(1 - BINARY_LIKELIHOODS["TOC"][feature])
            log_p_not_toc += np.log(1 - BINARY_LIKELIHOODS["NOT_TOC"][feature])

    # Handle numerical features
    for feature, value in numerical_features.items():
        toc_params = NUMERICAL_DISTRIBUTIONS["TOC"][feature]
        not_toc_params = NUMERICAL_DISTRIBUTIONS["NOT_TOC"][feature]

        p_toc = poisson_pdf(value, toc_params["lambda"])
        p_not_toc = poisson_pdf(value, not_toc_params["lambda"])

        log_p_toc += np.log(p_toc + 1e-10)
        log_p_not_toc += np.log(p_not_toc + 1e-10)

    # Normalize
    log_sum = np.logaddexp(log_p_toc, log_p_not_toc)
    return np.exp(log_p_toc - log_sum)


def detect_toc(page_text: str) -> bool:
    has_contents_keyword = "contents" in page_text.lower()
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
            "has_contents_keyword": has_contents_keyword,
            "has_roman_numerals": has_roman_numerals,
            "has_word_index_reference_bibliography_keywords": has_word_index_reference_bibliography_keywords,
        },
        "numerical_features": {"number_of_page_numbers": number_of_page_numbers},
    }
    return (
        predict(features["binary_features"], features["numerical_features"])
        > TOC_DETECTION_THRESHOLD
    )  # threshold for TOC detection


if __name__ == "__main__":
    test_samples = [
        {
            "binary_features": {
                "has_contents_keyword": True,
                "has_roman_numerals": True,
                "has_word_index_reference_bibliography_keywords": True,
            },
            "numerical_features": {"number_of_page_numbers": 10},
        },
        {
            "binary_features": {
                "has_contents_keyword": False,
                "has_roman_numerals": True,
                "has_word_index_reference_bibliography_keywords": True,
            },
            "numerical_features": {"number_of_page_numbers": 10},
        },
        {
            "binary_features": {
                "has_contents_keyword": True,
                "has_roman_numerals": False,
                "has_word_index_reference_bibliography_keywords": True,
            },
            "numerical_features": {"number_of_page_numbers": 10},
        },
        {
            "binary_features": {
                "has_contents_keyword": False,
                "has_roman_numerals": True,
                "has_word_index_reference_bibliography_keywords": False,
            },
            "numerical_features": {"number_of_page_numbers": 10},
        },
    ]
    for sample in test_samples:
        print(f"Sample: {sample}")
        print(f"Probability of TOC: {predict(sample['binary_features'], sample['numerical_features'])}")
