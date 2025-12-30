use crate::config::ProviderConfig;
use llm::{LLMProvider, builder::LLMBuilder};
use secret_string::SecretString;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ModelError {
    #[error("API key is missing")]
    MissingApiKey(String),

    #[error("LLM Client Error")]
    LLMClientError(#[from] llm::error::LLMError),
}

fn build_llm_client(config: &ProviderConfig) -> Result<Box<dyn LLMProvider>, ModelError> {
    let api_key =
        std::env::var("LAZYREADER_LLM_KEY").expect("LAZYREADER_LLM_KEY not set in environment");

    LLMBuilder::new()
        .backend(config.llm_backend.clone())
        .api_key(api_key)
        .model(config.llm_model.clone())
        .max_tokens(8192)
        .temperature(0.7)
        .build()
        .map_err(ModelError::LLMClientError)
}

struct LLMPool {
    api_key: SecretString<String>,
    cancellation_token: tokio_util::sync::CancellationToken,
}
