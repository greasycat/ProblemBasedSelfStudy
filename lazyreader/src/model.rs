use crate::config::ProviderConfig;
use crate::job::{BoxFuture, JobFn, JobHandle, JobPool, JobStatus};

use llm::chat::{ChatMessage, ChatResponse, StructuredOutputFormat};
use llm::{LLMProvider, builder::LLMBackend, builder::LLMBuilder};
use secret_string::SecretString;
use thiserror::Error;

macro_rules! unwrap_or_return {
    ($stmt:expr, $handle:expr) => {
        match $stmt {
            Ok(t) => t,
            Err(e) => {
                $handle.set_status(JobStatus::Failed(e.to_string()));
                return;
            }
        }
    };
}

#[macro_export]
macro_rules! text_only_messages {
    ($($content:expr),*$(,)?) => {
        vec![$(llm::chat::ChatMessage::user().content($content).build(),)*]
    };
}

#[derive(Error, Debug)]
pub enum ModelError {
    #[error("API key is missing")]
    MissingApiKey(String),

    #[error("LLM Client Error")]
    LLMClientError(#[from] llm::error::LLMError),

    #[error("Unsupported LLM backend")]
    UnsupportedLLMBackend(LLMBackend),

    #[error("Empty Response")]
    EmptyResponse,
}

#[derive(Clone)]
pub struct VariantLLMBuilder {
    backend: LLMBackend,
    model: String,
    max_tokens: u32,
    temperature: f32,
    api_key: SecretString<String>,
}

impl VariantLLMBuilder {
    pub fn from_config(provider_config: ProviderConfig) -> Result<Self, ModelError> {
        let api_key = Self::get_api_key_from_env(provider_config.llm_backend.clone())?;
        Ok(Self {
            backend: provider_config.llm_backend.clone(),
            model: provider_config.llm_model.clone(),
            max_tokens: 8192,
            temperature: 0.7,
            api_key,
        })
    }

    fn default_builder(&self) -> LLMBuilder {
        LLMBuilder::new()
            .backend(self.backend.clone())
            .api_key(self.api_key.value())
            .model(self.model.clone())
            .max_tokens(self.max_tokens)
            .temperature(self.temperature)
    }

    pub fn standard_provider(&self) -> Result<Box<dyn LLMProvider>, ModelError> {
        Ok(self.default_builder().build()?)
    }

    pub fn schema_provider(
        &self,
        schema: StructuredOutputFormat,
    ) -> Result<Box<dyn LLMProvider>, ModelError> {
        Ok(self.default_builder().schema(schema).build()?)
    }

    fn get_api_key_from_env(llm_backend: LLMBackend) -> Result<SecretString<String>, ModelError> {
        match llm_backend {
            LLMBackend::Google => Ok(SecretString::new(
                std::env::var("GOOGLE_API_KEY")
                    .map_err(|_| ModelError::MissingApiKey("GOOGLE_API_KEY".to_string()))?,
            )),
            _ => Err(ModelError::UnsupportedLLMBackend(llm_backend)),
        }
    }
}

pub struct Model {
    builder: VariantLLMBuilder,
    job_pool: JobPool,
}

impl Model {
    pub fn new(job_pool: JobPool, provider_config: ProviderConfig) -> Result<Self, ModelError> {
        let builder = VariantLLMBuilder::from_config(provider_config)?;
        Ok(Self { builder, job_pool })
    }

    fn submit_job(&mut self, job: JobFn) -> String {
        let job_id = self.job_pool.submit_job(job);
        job_id
    }
    pub fn submit_text_only_job(&mut self, messages: Vec<ChatMessage>) -> String {
        let builder = self.builder.clone();
        self.submit_job(create_text_only_job(builder, messages))
    }

    pub fn submit_schema_job(
        &mut self,
        messages: Vec<ChatMessage>,
        schema: StructuredOutputFormat,
    ) -> String {
        let builder = self.builder.clone();
        self.submit_job(create_schema_job(builder, messages, schema))
    }

    pub fn get_job_status(&self, job_id: &str) -> Option<JobStatus> {
        self.job_pool.get_job_status(job_id)
    }
}

fn create_text_only_job(builder: VariantLLMBuilder, messages: Vec<ChatMessage>) -> JobFn {
    Box::new(move |handle: JobHandle| -> BoxFuture {
        Box::pin(async move {
            let provider: Box<dyn LLMProvider> =
                unwrap_or_return!(builder.standard_provider(), handle);

            let response: Box<dyn ChatResponse> =
                unwrap_or_return!(provider.chat(&messages).await, handle);

            let text: String =
                unwrap_or_return!(response.text().ok_or(ModelError::EmptyResponse), handle);

            handle.set_status(JobStatus::Completed(text));
        })
    })
}

fn create_schema_job(
    builder: VariantLLMBuilder,
    messages: Vec<ChatMessage>,
    schema: StructuredOutputFormat,
) -> JobFn {
    Box::new(move |handle: JobHandle| -> BoxFuture {
        Box::pin(async move {
            let provider: Box<dyn LLMProvider> =
                unwrap_or_return!(builder.schema_provider(schema), handle);

            let response: Box<dyn ChatResponse> =
                unwrap_or_return!(provider.chat(&messages).await, handle);

            let text: String =
                unwrap_or_return!(response.text().ok_or(ModelError::EmptyResponse), handle);

            handle.set_status(JobStatus::Completed(text));
        })
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    async fn wait_for_job_to_complete(model: &mut Model, job_id: &str) -> Option<String> {
        use std::time::{Duration, Instant};
        let timeout = Duration::from_secs(15);
        let interval = Duration::from_millis(1000);
        let start = Instant::now();

        let mut response: Option<String> = None;

        loop {
            if start.elapsed() > timeout {
                assert!(false, "Timeout waiting for job to complete");
                break;
            }

            if let Some(status) = model.get_job_status(job_id) {
                match status {
                    JobStatus::Completed(r) => {
                        response = Some(r);
                        break;
                    }
                    JobStatus::Pending => {}
                    JobStatus::InProgress => {}
                    JobStatus::Failed(error) => {
                        assert!(false, "Job failed: {error}");
                        break;
                    }
                }
            }
            tokio::time::sleep(interval).await;
        }

        response
    }

    #[tokio::test]
    async fn test_model_with_schema() {
        let schema = include_str!("../tests/schemas/capitals.json");

        let schema: StructuredOutputFormat = serde_json::from_str(schema).unwrap();
        let mut model = Model::new(JobPool::new(), ProviderConfig::default()).unwrap();
        let job_id = model.submit_schema_job(
            text_only_messages!(
                "Extract information from the following text using the provided JSON schema",
                "France: Paris, Germany: Berlin, Italy: Rome"
            ),
            schema,
        );
        let response = wait_for_job_to_complete(&mut model, &job_id).await;
        assert!(response.is_some());
        let response = response.unwrap();
        println!("Response: {response}");
        assert!(response.to_lowercase().contains("paris"));
        assert!(response.to_lowercase().contains("berlin"));
        assert!(response.to_lowercase().contains("rome"));
    }

    #[tokio::test]
    async fn test_model() {
        let mut model = Model::new(JobPool::new(), ProviderConfig::default()).unwrap();
        let job_id =
            model.submit_text_only_job(text_only_messages!("What is the capital of France?"));
        let response = wait_for_job_to_complete(&mut model, &job_id).await;
        assert!(response.is_some());
        assert!(response.unwrap().to_lowercase().contains("paris"));
    }
}
