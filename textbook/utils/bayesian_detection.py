import math
from typing import Dict
import numpy as np

def poisson_pdf(x: int, lambda_value: float) -> float:
    return (lambda_value**x * math.exp(-lambda_value)) / math.factorial(x)

def predict(
    binary_features: Dict[str, bool], numerical_features: Dict[str, int], prior: float, binary_likelihoods: Dict[str, Dict[str, float]], numerical_distributions: Dict[str, Dict[str, Dict[str, int]]]
) -> float:
    log_p_true = np.log(prior)
    log_p_false = np.log(1 - prior)

    # Handle binary features
    for feature, observed in binary_features.items():
        if observed:
            log_p_true += np.log(binary_likelihoods["TRUE"][feature])
            log_p_false += np.log(binary_likelihoods["FALSE"][feature])
        else:
            log_p_true += np.log(1 - binary_likelihoods["TRUE"][feature])
            log_p_false += np.log(1 - binary_likelihoods["FALSE"][feature])

    # Handle numerical features
    for feature, value in numerical_features.items():
        true_params = numerical_distributions["TRUE"][feature]
        false_params = numerical_distributions["FALSE"][feature]

        p_true = poisson_pdf(value, true_params["lambda"])
        p_false = poisson_pdf(value, false_params["lambda"])

        log_p_true += np.log(p_true + 1e-10)
        log_p_false += np.log(p_false + 1e-10)

    # Normalize
    log_sum = np.logaddexp(log_p_true, log_p_false)
    return np.exp(log_p_true - log_sum)

def create_binary_likelihood_dict(param_list: list[tuple[str, float, float]]) -> dict[str, dict[str, float]]:
    true_likelihood_dict = {}
    false_likelihood_dict = {}
    for name, true_likelihood, false_likelihood in param_list:
        true_likelihood_dict[name] = true_likelihood
        false_likelihood_dict[name] = false_likelihood
    return {"TRUE": true_likelihood_dict, "FALSE": false_likelihood_dict}

def create_distribution_dict(param_list: list[tuple[str, int, int]]) -> Dict[str, Dict[str, Dict[str, int]]]:
    true_distribution = {}
    false_distribution = {}
    for name, true_lambda, false_lambda in param_list:
        true_distribution[name] = {"lambda": true_lambda}
        false_distribution[name] = {"lambda": false_lambda}
    return {"TRUE": true_distribution, "FALSE": false_distribution}