#![allow(unused_imports)] // TODO: Remove this line when all imports are used

use axum::Json;
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::{Router, extract::MatchedPath, routing::get};
use lazyreader::config::try_create_or_load_config;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use serde_json::json;
use tokio::net::TcpListener;
use tower_http::trace::TraceLayer;
use tracing::{info, info_span, instrument};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

// Tracing Setup
fn init_tracing() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| {
                format!(
                    "{}=debug,tower_http=debug,axum::rejection=trace",
                    env!("CARGO_CRATE_NAME")
                )
                .into()
            }),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();
}

#[tokio::main]
async fn main() {
    init_tracing();
    let config = try_create_or_load_config().expect("Failed to load or create config");
    let address = format!("{}:{}", config.server.addr, config.server.port);

    let app = Router::new().route("/", get(check_health)).layer(
        TraceLayer::new_for_http().make_span_with(|request: &axum::http::Request<_>| {
            let path = request
                .extensions()
                .get::<MatchedPath>()
                .map(MatchedPath::as_str);
            info_span!("http_request", path)
        }),
    );
    let listener = TcpListener::bind(address).await.unwrap();

    info!("Server now running on {}", listener.local_addr().unwrap());

    axum::serve(listener, app).await.unwrap();
}

async fn check_health() -> Json<Value> {
    Json(json!({"status": "ok"}))
}
