use proxy_wasm::traits::*;
use proxy_wasm::types::*;
use serde::Deserialize;
use std::collections::HashSet;
use log::{info, warn};

// -----------------------------------------------------------------------------
// 1. Data Structures (Genetic Memory)
// -----------------------------------------------------------------------------

#[derive(Deserialize, Debug, Clone, Default)]
struct PolicyConfig {
    #[serde(default)]
    suppression_paths: HashSet<String>, // R_epi: Methylation targets
    #[serde(default)]
    allow_paths: HashSet<String>,       // M_star: Whitelist
}

struct LeukocyteRoot {
    config: PolicyConfig,
}

impl Context for LeukocyteRoot {}

impl RootContext for LeukocyteRoot {
    fn on_configure(&mut self, _plugin_configuration_size: usize) -> bool {
        if let Some(config_bytes) = self.get_plugin_configuration() {
            if let Ok(config_str) = std::str::from_utf8(&config_bytes) {
                if let Ok(mut config) = serde_json::from_str::<PolicyConfig>(config_str) {
                    // Normalize to lowercase for header matching (Envoy uses lowercase headers)
                    config.suppression_paths = config.suppression_paths.into_iter()
                        .map(|s| s.to_lowercase())
                        .collect();
                    config.allow_paths = config.allow_paths.into_iter()
                        .map(|s| s.to_lowercase())
                        .collect();

                    info!("🧬 [Leukocyte] Configuration Transduced: {} suppression paths, {} allow paths", 
                          config.suppression_paths.len(), config.allow_paths.len());
                    self.config = config;
                    return true;
                }
            }
        }
        warn!("⚠️ [Leukocyte] Failed to load configuration (Immunity Deficit)");
        true
    }

    fn create_http_context(&self, _context_id: u32) -> Option<Box<dyn HttpContext>> {
        Some(Box::new(LeukocyteFilter {
            config: self.config.clone(),
        }))
    }

    fn get_type(&self) -> Option<ContextType> {
        Some(ContextType::HttpContext)
    }
}

struct LeukocyteFilter {
    config: PolicyConfig,
}

impl Context for LeukocyteFilter {}

impl LeukocyteFilter {
    fn send_denial(&mut self, reason: &str, defense_type: &str) {
        let headers = self.get_http_request_headers();
        let is_grpc = headers.iter().any(|(k, v)| k.to_lowercase() == "content-type" && v.to_lowercase().contains("application/grpc"));

        if is_grpc {
            self.send_http_response(
                200,
                vec![
                    ("content-type", "application/grpc"),
                    ("x-leukocyte-defense", defense_type),
                    ("grpc-status", "7"), // PermissionDenied
                    ("grpc-message", reason),
                ],
                None,
            );
        } else {
             self.send_http_response(
                403,
                vec![("x-leukocyte-defense", defense_type)],
                Some(reason.as_bytes()),
            );
        }
    }
}

impl HttpContext for LeukocyteFilter {

    fn on_http_request_headers(&mut self, _num_headers: usize, _end_of_stream: bool) -> Action {
        let headers = self.get_http_request_headers();
        for (name, _value) in headers {
            if self.config.suppression_paths.contains(&name) || 
               self.config.suppression_paths.contains(&name.to_lowercase()) {
                warn!("🛡️ [Methylation] Suppressed expression of pathogen header: {}", name);
                self.send_denial("Access Denied: Pathogen Header Suppressed", "methylated-header");
                return Action::Pause;
            }
        }

        if !self.config.suppression_paths.is_empty() || !self.config.allow_paths.is_empty() {
            return Action::Continue;
        }
        Action::Continue
    }

    fn on_http_request_body(&mut self, body_size: usize, end_of_stream: bool) -> Action {
        if !end_of_stream {
            return Action::Pause;
        }

        if let Some(body_bytes) = self.get_http_request_body(0, body_size) {
            if let Ok(json_body) = serde_json::from_slice::<serde_json::Value>(&body_bytes) {
                let flat_paths = flatten_json(&json_body, "");
                
                // 1. Epigenetic Suppression
                for param in &flat_paths {
                    if self.config.suppression_paths.contains(param) {
                        warn!("🛡️ [Methylation] Suppressed expression of pathogen path: {}", param);
                        self.send_denial("Access Denied: Pathogen Suppressed", "methylated");
                        return Action::Pause;
                    }
                }

                // 2. Hierarchical Purity
                if !self.config.allow_paths.is_empty() {
                     for param in &flat_paths {
                        if !self.config.allow_paths.contains(param) {
                             warn!("⚔️ [Immunity] Foreign antigen detected (Not in Allow Map): {}", param);
                             self.send_denial("Access Denied: Foreign Antigen", "antigen-rejected");
                             return Action::Pause;
                        }
                    }
                }
            }
        }

        Action::Continue
    }
}

// -----------------------------------------------------------------------------
// Helper: Flatten JSON (The transcription process)
// -----------------------------------------------------------------------------
fn flatten_json(value: &serde_json::Value, prefix: &str) -> Vec<String> {
    let mut paths = Vec::new();
    
    match value {
        serde_json::Value::Object(map) => {
            for (k, v) in map {
                let new_key = if prefix.is_empty() {
                    k.clone()
                } else {
                    format!("{}.{}", prefix, k)
                };
                paths.push(new_key.clone());
                paths.extend(flatten_json(v, &new_key));
            }
        }
        serde_json::Value::Array(arr) => {
             // Treat array indices as separate paths? Or ignore?
             // Common practice: flatten with [i] or just recurse.
             // Simpler for this demo: just recurse into objects
             for v in arr {
                 paths.extend(flatten_json(v, prefix));
             }
        }
        _ => {}
    }
    paths
}

// -----------------------------------------------------------------------------
// Entry Point
// -----------------------------------------------------------------------------
proxy_wasm::main! {{
    proxy_wasm::set_log_level(LogLevel::Trace);
    proxy_wasm::set_root_context(|_| -> Box<dyn RootContext> {
        Box::new(LeukocyteRoot {
            config: PolicyConfig::default(),
        })
    });
}}
