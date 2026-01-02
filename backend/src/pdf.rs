use crate::config::ProviderConfig;

use derive_builder::Builder;
use pdf2image::{PDF as PDF2Image, PDF2ImageError, Pages, RenderOptionsBuilder, image};
use reqwest::Client;
use reqwest::multipart;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::{io, ops::RangeInclusive, path::Path};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum PDFError {
    #[error("Request parameters build error: {0}")]
    RequestParametersBuildError(#[from] MinerURequestBuilderError),
    #[error("Request error")]
    RequestError(#[from] reqwest::Error),
    #[error("Multipart error")]
    MultipartError(#[from] io::Error),
    #[error("Markdown not found in response")]
    MarkdownNotFound,
    #[error("Response is not OK: {0}")]
    ResponseNotOK(String),
    #[error("JSON deserialization error: {0}")]
    JSONDeserializationError(#[from] serde_json::Error),
    #[error("PDF2Image error: {0}")]
    PDF2ImageError(#[from] PDF2ImageError),
    #[error("Render options build error: {0}")]
    RenderOptionsBuildError(String),
}

#[derive(Debug, Serialize, Deserialize, Clone, Builder)]
pub struct MinerURequest {
    #[builder(default = "./output".to_string())]
    output_dir: String,
    #[builder(default = vec!["en".to_string()])]
    lang_list: Vec<String>,
    #[builder(default = "pipeline".to_string())]
    backend: String,
    #[builder(default = "ocr".to_string())]
    parse_method: String,
    #[builder(default = true)]
    formula_enable: bool,
    #[builder(default = true)]
    table_enable: bool,
    #[builder(default = true)]
    return_md: bool,
    #[builder(default = false)]
    return_middle_json: bool,
    #[builder(default = false)]
    return_model_output: bool,
    #[builder(default = false)]
    return_content_list: bool,
    #[builder(default = false)]
    return_images: bool,
    #[builder(default = false)]
    response_format_zip: bool,
    #[builder(default = 0)]
    start_page_id: u32,
    #[builder(default = 99999)]
    end_page_id: u32,
}

impl MinerURequest {
    async fn create_multipart(&self, file: &Path) -> Result<multipart::Form, PDFError> {
        let form = multipart::Form::new()
            .part(
                "files",
                multipart::Part::file(file)
                    .await?
                    .mime_str("application/pdf")?,
            )
            .text("output_dir", self.output_dir.clone())
            .text("lang_list", self.lang_list.join(","))
            .text("backend", self.backend.clone())
            .text("parse_method", self.parse_method.clone())
            .text("formula_enable", self.formula_enable.to_string())
            .text("table_enable", self.table_enable.to_string())
            .text("return_md", self.return_md.to_string())
            .text("return_middle_json", self.return_middle_json.to_string())
            .text("return_model_output", self.return_model_output.to_string())
            .text("return_content_list", self.return_content_list.to_string())
            .text("return_images", self.return_images.to_string())
            .text("response_format_zip", self.response_format_zip.to_string())
            .text("start_page_id", self.start_page_id.to_string())
            .text("end_page_id", self.end_page_id.to_string());
        Ok(form)
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct FileContent {
    md_content: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct MinerUResponse {
    results: HashMap<String, FileContent>,
}

impl MinerUResponse {
    fn get_markdown(&mut self) -> Option<String> {
        // get the first key
        let first_key = self.results.keys().next()?.clone();
        let content = self.results.remove(&first_key)?;
        Some(content.md_content)
    }
}

pub struct PDF {
    client: Client,
    providier_config: ProviderConfig,
}

impl PDF {
    pub fn new(provider_config: ProviderConfig) -> Self {
        Self {
            client: Client::new(),
            providier_config: provider_config,
        }
    }

    pub async fn ocr(
        &self,
        file: &Path,
        request_params: MinerURequest,
    ) -> Result<String, PDFError> {
        let multipart = request_params.create_multipart(file).await?;

        let response = self
            .client
            .post(format!(
                "http://{}:{}/file_parse",
                self.providier_config.mineru_addr, self.providier_config.mineru_port
            ))
            .multipart(multipart)
            .send()
            .await?;
        // check if the response is ok
        if !response.status().is_success() {
            return Err(PDFError::ResponseNotOK(
                response.error_for_status()?.text().await?,
            ));
        }
        let mut response = response.json::<MinerUResponse>().await?;
        Ok(response.get_markdown().ok_or(PDFError::MarkdownNotFound)?)
    }

    pub async fn pdf_to_images(
        &self,
        file: &Path,
        page_range: RangeInclusive<u32>,
    ) -> Result<Vec<image::DynamicImage>, PDFError> {
        let pdf = PDF2Image::from_file(file)?;
        let images = pdf.render(
            Pages::Range(page_range),
            RenderOptionsBuilder::default()
                .build()
                .map_err(|e| PDFError::RenderOptionsBuildError(e.to_string()))?,
        )?;
        Ok(images)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_ocr() {
        let pdf = PDF::new(ProviderConfig::default());
        let request_params = MinerURequestBuilder::default()
            .start_page_id(0)
            .build()
            .unwrap();
        let markdown = pdf
            .ocr(&Path::new("./tests/pdfs/hello_world.pdf"), request_params)
            .await
            .unwrap();
        println!("{}", markdown);
        assert!(markdown.to_lowercase().contains("hello"));

        let request_params = MinerURequestBuilder::default()
            .start_page_id(1)
            .end_page_id(1)
            .build()
            .unwrap();
        let markdown = pdf
            .ocr(&Path::new("./tests/pdfs/wikipedia.pdf"), request_params)
            .await
            .unwrap();
        println!("{}", markdown);
        assert!(markdown.to_lowercase().contains("technical details"));

        let request_params = MinerURequestBuilder::default()
            .start_page_id(0)
            .formula_enable(false)
            .build()
            .unwrap();
        let markdown = pdf
            .ocr(&Path::new("./tests/pdfs/wikipedia.png"), request_params)
            .await
            .unwrap();
        println!("{}", markdown);
        assert!(markdown.to_lowercase().contains("encyclopedia"));
        assert!(!markdown.to_lowercase().contains("begin"));
    }
}
