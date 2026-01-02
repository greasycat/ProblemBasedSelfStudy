use llm::builder::LLMBackend;
use serde::{Deserialize, Serialize};
use thiserror::Error;
use tracing::{instrument, warn};

#[derive(Error, Debug)]
pub enum ConfigError {
    #[error("Configuration Load Error")]
    ConfigLoadError(#[from] config::ConfigError),

    #[error("IO Error")]
    IOError(#[from] std::io::Error),

    #[error("Deserialize Error")]
    TomlSerializationEror(#[from] toml::ser::Error),
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ServerConfig {
    pub addr: String,
    pub port: u16,
}

impl Default for ServerConfig {
    fn default() -> Self {
        ServerConfig {
            addr: "0.0.0.0".to_string(),
            port: 8765,
        }
    }
}


#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ProviderConfig {
    pub mineru_addr: String,
    pub mineru_port: u16,

    #[serde(with = "LLMBackendDef")]
    pub llm_backend: LLMBackend,
    pub llm_model: String,
}

impl Default for ProviderConfig {
    fn default() -> Self {
        ProviderConfig {
            mineru_addr: "localhost".to_string(),
            mineru_port: 8848,
            llm_backend: LLMBackend::Google,
            llm_model: "gemini-3-pro-preview".to_string(),
        }
    }
}


#[derive(Debug, Default, Serialize, Deserialize, Clone)]
pub struct Config {
    pub server: ServerConfig,
    pub provider: ProviderConfig,
}

pub fn load_config(path: &std::path::Path) -> Result<Config, ConfigError> {
    Ok(config::Config::builder()
        .add_source(config::File::from(path))
        .add_source(config::Environment::with_prefix("LAZYREADER"))
        .build()?
        .try_deserialize::<Config>()?)
}

pub fn create_default_config(path: &std::path::Path) -> Result<(), ConfigError> {
    let default_config = Config::default();
    let toml_string = toml::to_string(&default_config)?;
    std::fs::write(path, toml_string)?;
    Ok(())
}

#[instrument]
pub fn try_create_or_load_config() -> Result<Config, ConfigError> {
    let mut paths_to_check = Vec::new();

    if let Ok(dir) = std::env::current_dir() {
        paths_to_check.push(dir.join("config.toml"));
    }

    if let Some(dir) = dirs::config_dir() {
        paths_to_check.push(dir.join("lazyreader").join("config.toml"));
    }

    for path in &paths_to_check {
        if path.exists()
            && let Ok(config) = load_config(path)
        {
            return Ok(config);
        }
    }

    warn!(
        "No valid config found, creating default config at {:?}",
        paths_to_check[0]
    );
    create_default_config(&paths_to_check[0])?;
    load_config(&paths_to_check[0])
}

#[cfg(test)]
mod tests {
    use super::*;
    use toml;
    use uuid::Uuid;

    struct TempFile {
        path: std::path::PathBuf,
    }

    impl TempFile {
        fn new(toml_string: &str) -> Self {
            let path = std::env::current_dir()
                .unwrap()
                .join(format!("config_{}.toml", Uuid::new_v4()));
            std::fs::write(&path, toml_string).unwrap();
            TempFile { path }
        }
    }

    impl Drop for TempFile {
        fn drop(&mut self) {
            let _ = std::fs::remove_file(&self.path);
        }
    }

    #[test]
    fn test_default_config_should_pass() {
        let toml = toml::to_string(&Config::default()).unwrap();

        let temp_file = TempFile::new(&toml);
        let config = load_config(&temp_file.path).unwrap();
        assert_eq!(config.server.addr, "0.0.0.0");
        assert_eq!(config.server.port, 8765);
        assert_eq!(config.provider.mineru_addr, "localhost");
        assert_eq!(config.provider.mineru_port, 8000);
    }

    #[test]
    fn test_create_and_load_problematic_config() {
        let toml_string = r#"
[server]
addr = 0.0.0.0
port = 8765

[provider]
mineru_addr = localhost
mineru_port = 8000
            "#;
        let temp_file = TempFile::new(toml_string);
        let config = load_config(&temp_file.path);
        assert!(config.is_err());
    }
    #[test]
    fn test_missing_field_should_fail() {
        let toml_string = r#"
[server]
addr = "0.0.0.0"
port = 8765
"#;
        let temp_file = TempFile::new(toml_string);
        let config = load_config(&temp_file.path);
        assert!(config.is_err());
    }
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(remote = "LLMBackend")]
pub enum LLMBackendDef {
    /// OpenAI API provider (GPT-3, GPT-4, etc.)
    OpenAI,
    /// Anthropic API provider (Claude models)
    Anthropic,
    /// Ollama local LLM provider for self-hosted models
    Ollama,
    /// DeepSeek API provider for their LLM models
    DeepSeek,
    /// X.AI (formerly Twitter) API provider
    XAI,
    /// Phind API provider for code-specialized models
    Phind,
    /// Google Gemini API provider
    Google,
    /// Groq API provider
    Groq,
    /// Azure OpenAI API provider
    AzureOpenAI,
    /// ElevenLabs API provider
    ElevenLabs,
    /// Cohere API provider
    Cohere,
    /// Mistral API provider
    Mistral,
    /// OpenRouter API provider
    OpenRouter,
    /// HuggingFace Inference Providers API
    HuggingFace,
}