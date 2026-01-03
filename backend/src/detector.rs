use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum DetectorError {
    #[error("Parameter map is none for parameter type: {0}")]
    ParameterMapNone(String),
    #[error("Bernoulli parameter not found for key: {0}")]
    BernoulliParameterNotFound(String),
    #[error("Poisson parameter not found for key: {0}")]
    PoissonParameterNotFound(String),
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct BernoulliParameters {
    p_true: f64,
    p_false: f64,
    weight: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PoissonParameters {
    lambda_true: f64,
    lambda_false: f64,
    weight: f64,
}

pub struct BayesDetectorBuilder {
    detector: BayesDetector,
}

impl BayesDetectorBuilder {
    pub fn new() -> Self {
        Self {
            detector: BayesDetector {
                bernoulli_parameters: Some(HashMap::new()),
                poisson_parameters: Some(HashMap::new()),
            },
        }
    }

    pub fn bernoulli_parameter(self, key: &'static str, p_true: f64, p_false: f64) -> Self {
        self.bernoulli_parameter_with_weight(key, p_true, p_false, 1.0)
    }

    pub fn bernoulli_parameter_with_weight(
        mut self,
        key: &'static str,
        p_true: f64,
        p_false: f64,
        weight: f64,
    ) -> Self {
        self.detector.bernoulli_parameters.as_mut().map(|h| {
            h.insert(
                key.to_owned(),
                BernoulliParameters {
                    p_true,
                    p_false,
                    weight,
                },
            )
        });
        self
    }

    pub fn poisson_parameter(self, key: &'static str, lambda_true: f64, lambda_false: f64) -> Self {
        self.poisson_parameter_with_weight(key, lambda_true, lambda_false, 1.0)
    }
    pub fn poisson_parameter_with_weight(
        mut self,
        key: &'static str,
        lambda_true: f64,
        lambda_false: f64,
        weight: f64,
    ) -> Self {
        self.detector.poisson_parameters.as_mut().map(|h| {
            h.insert(
                key.to_owned(),
                PoissonParameters {
                    lambda_true,
                    lambda_false,
                    weight,
                },
            )
        });
        self
    }

    pub fn build(self) -> BayesDetector {
        self.detector
    }
}

pub enum DetectorValue {
    Bernoulli(bool),
    Poisson(u32),
}

pub struct DetectorDataBuilder {
    data_map: HashMap<String, DetectorValue>,
}

impl DetectorDataBuilder {
    pub fn new() -> Self {
        Self {
            data_map: HashMap::new(),
        }
    }
}

impl DetectorDataBuilder {
    pub fn add_bernoulli_value(mut self, key: &'static str, value: bool) -> Self {
        self.data_map
            .insert(key.to_owned(), DetectorValue::Bernoulli(value));
        self
    }
}

impl DetectorDataBuilder {
    pub fn add_poisson_value(mut self, key: &'static str, value: u32) -> Self {
        self.data_map
            .insert(key.to_owned(), DetectorValue::Poisson(value));
        self
    }
}

impl DetectorDataBuilder {
    pub fn build(self) -> HashMap<String, DetectorValue> {
        self.data_map
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DetectionResult {
    pub is_true: bool,
    pub probability: f64,
    pub true_likelihood: f64,
    pub false_likelihood: f64,
    pub llr_contributions: HashMap<String, f64>,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct BayesDetector {
    bernoulli_parameters: Option<HashMap<String, BernoulliParameters>>,
    poisson_parameters: Option<HashMap<String, PoissonParameters>>,
}

impl BayesDetector {
    pub fn detect(
        &self,
        data_map: HashMap<String, DetectorValue>,
        prior_true: f64,
    ) -> Result<DetectionResult, DetectorError> {
        let mut total_true_likelihood = prior_true.ln();
        let mut total_false_likelihood = (1.0 - prior_true).ln();
        let mut llr_contributions = HashMap::new();
        for (key, value) in data_map.iter() {
            match value {
                DetectorValue::Bernoulli(value) => {
                    let bernoulli_parameter = self
                        .bernoulli_parameters
                        .as_ref()
                        .ok_or(DetectorError::ParameterMapNone("bernoulli".to_string()))?
                        .get(key)
                        .ok_or(DetectorError::BernoulliParameterNotFound(key.clone()))?;

                    let true_likelihood = bernoulli_pmf(*value, bernoulli_parameter.p_true);
                    let false_likelihood = bernoulli_pmf(*value, bernoulli_parameter.p_false);

                    total_true_likelihood += bernoulli_parameter.weight * true_likelihood.ln();
                    total_false_likelihood += bernoulli_parameter.weight * false_likelihood.ln();

                    llr_contributions.insert(key.clone(), true_likelihood - false_likelihood);
                }
                DetectorValue::Poisson(value) => {
                    let poisson_parameter = self
                        .poisson_parameters
                        .as_ref()
                        .ok_or(DetectorError::ParameterMapNone("poisson".to_string()))?
                        .get(key)
                        .ok_or(DetectorError::PoissonParameterNotFound(key.clone()))?;

                    let true_likelihood = poisson_pmf(*value, poisson_parameter.lambda_true);
                    let false_likelihood = poisson_pmf(*value, poisson_parameter.lambda_false);

                    total_true_likelihood += poisson_parameter.weight * true_likelihood.ln();
                    total_false_likelihood += poisson_parameter.weight * false_likelihood.ln();

                    llr_contributions.insert(key.clone(), true_likelihood - false_likelihood);
                }
            }
        }
        let probability = 1.0 / (1.0 + (total_false_likelihood - total_true_likelihood).exp());
        Ok(DetectionResult {
            is_true: total_true_likelihood > total_false_likelihood,
            probability,
            true_likelihood: total_true_likelihood,
            false_likelihood: total_false_likelihood,
            llr_contributions,
        })
    }
}

fn bernoulli_pmf(value: bool, p: f64) -> f64 {
    if value { p } else { 1.0 - p }
}

fn poisson_pmf(value: u32, lambda: f64) -> f64 {
    lambda.powf(value as f64) * (-lambda).exp() / factorial(value) as f64
}

fn factorial(num: u32) -> u32 {
    (1..=num).product()
}

#[cfg(test)]
mod tests {
    use super::*;

    use float_cmp::approx_eq;

    #[test]
    fn test_factorial() {
        assert_eq!(factorial(0), 1);
        assert_eq!(factorial(1), 1);
        assert_eq!(factorial(2), 2);
        assert_eq!(factorial(3), 6);
        assert_eq!(factorial(4), 24);
        assert_eq!(factorial(5), 120);
    }

    #[test]
    fn test_bernoulli_pmf() {
        assert!(approx_eq!(
            f64,
            bernoulli_pmf(true, 0.7),
            0.7,
            epsilon = 1e-10
        ));
        assert!(approx_eq!(
            f64,
            bernoulli_pmf(false, 0.7),
            0.3,
            epsilon = 1e-10
        ));
    }

    #[test]
    fn test_poisson_pmf() {
        let d1 = poisson_pmf(0, 1.0);
        let d2 = poisson_pmf(1, 1.0);
        let d3 = poisson_pmf(2, 1.0);
        let d4 = poisson_pmf(3, 1.0);
        assert!(approx_eq!(f64, d1, 0.36787944117144233, epsilon = 1e-10));
        assert!(approx_eq!(f64, d2, 0.36787944117144233, epsilon = 1e-10));
        assert!(approx_eq!(f64, d3, 0.18393972058572116, epsilon = 1e-10));
        assert!(approx_eq!(f64, d4, 0.06131324019524038, epsilon = 1e-10));
    }

    #[test]
    fn test_detector_easy_case_true() {
        let detector = BayesDetectorBuilder::new()
            .bernoulli_parameter("word_contents_present", 0.7, 0.1)
            .bernoulli_parameter("word_index_bibliography_present", 0.95, 0.5)
            .poisson_parameter("word_chapter_count", 3.0, 1.0)
            .build();

        let data = DetectorDataBuilder::new()
            .add_bernoulli_value("word_contents_present", true)
            .add_bernoulli_value("word_index_bibliography_present", true)
            .add_poisson_value("word_chapter_count", 3)
            .build();

        let result = detector.detect(data, 0.65);
        assert!(result.is_ok());
        let result = result.unwrap();
        assert!(result.is_true);
        assert!(result.probability > 0.5);
        assert!(result.true_likelihood > result.false_likelihood);
        assert!(result.llr_contributions.len() == 3);
    }

    #[test]
    fn test_detector_medium_case_true() {
        let detector = BayesDetectorBuilder::new()
            .bernoulli_parameter("word_contents_present", 0.7, 0.5)
            .bernoulli_parameter("word_index_bibliography_present", 0.95, 0.5)
            .poisson_parameter_with_weight("word_chapter_count", 3.0, 1.0, 2.0)
            .build();

        let data = DetectorDataBuilder::new()
            .add_bernoulli_value("word_contents_present", false)
            .add_bernoulli_value("word_index_bibliography_present", false)
            .add_poisson_value("word_chapter_count", 3)
            .build();

        let result = detector.detect(data, 0.65);
        assert!(result.is_ok());
        let result = result.unwrap();
        assert!(result.is_true);
        assert!(result.probability > 0.5);
        assert!(result.true_likelihood > result.false_likelihood);
        assert!(result.llr_contributions.len() == 3);
    }

    #[test]
    fn test_detector_easy_case_false() {
        let detector = BayesDetectorBuilder::new()
            .bernoulli_parameter("word_contents_present", 0.7, 0.5)
            .bernoulli_parameter("word_index_bibliography_present", 0.95, 0.5)
            .poisson_parameter_with_weight("word_chapter_count", 3.0, 1.0, 2.0)
            .build();

        let data = DetectorDataBuilder::new()
            .add_bernoulli_value("word_contents_present", false)
            .add_bernoulli_value("word_index_bibliography_present", false)
            .add_poisson_value("word_chapter_count", 1)
            .build();

        let result = detector.detect(data, 0.65);
        println!("Result: {:#?}", result);
        assert!(result.is_ok());
        let result = result.unwrap();
        assert!(!result.is_true);
        assert!(result.probability < 0.5);
        assert!(result.true_likelihood < result.false_likelihood);
        assert!(result.llr_contributions.len() == 3);
    }
}
