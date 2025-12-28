use proxy_wasm::traits::*;
use proxy_wasm::types::*;
use serde::Deserialize;
use std::collections::{HashMap, HashSet};
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

impl HttpContext for LeukocyteFilter {
    fn on_http_request_headers(&mut self, _num_headers: usize, _end_of_stream: bool) -> Action {
        let headers = self.get_http_request_headers();
        for (name, _value) in headers {
            // [Enhancement] Log inspection for debug visibility
            // info!("🔍 Inspecting Header: {}", name); 

            // If the header name is in the suppression list, we block it (Methylation)
            if self.config.suppression_paths.contains(&name) || 
               self.config.suppression_paths.contains(&name.to_lowercase()) {
                warn!("🛡️ [Methylation] Suppressed expression of pathogen header: {}", name);
                self.send_http_response(
                    403,
                    vec![("x-leukocyte-defense", "methylated-header")],
                    Some(b"Access Denied: Pathogen Header Suppressed"),
                );
                return Action::Pause;
            }
        }

        // Only inspect bodies if we have policies.
        if !self.config.suppression_paths.is_empty() || !self.config.allow_paths.is_empty() {
             // Stop iteration to buffer the body
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
                // Flatten and Inspect
                let flat_paths = flatten_json(&json_body, "");
                
                // 1. Epigenetic Suppression (Methylation) - Priority 1
                for param in &flat_paths {
                    if self.config.suppression_paths.contains(param) {
                        warn!("🛡️ [Methylation] Suppressed expression of pathogen path: {}", param);
                        self.send_http_response(
                            403,
                            vec![("x-leukocyte-defense", "methylated")],
                            Some(b"Access Denied: Pathogen Suppressed"),
                        );
                        return Action::Pause;
                    }
                }

                // 2. Hierarchical Purity (Allowlist) - Priority 2
                // If allow_paths is set, we strictly enforce it.
                if !self.config.allow_paths.is_empty() {
                     for param in &flat_paths {
                        // Logic: If a path is NOT in allow_paths, we might want to block or scrub.
                        // For this implementation, we block if we see an unallowed path (Strict Immunity).
                        // Note: Real-world strict allowlisting is complex; this is a simplified model.
                        if !self.config.allow_paths.contains(param) {
                             // Check if a parent path is allowed (if we want to be permissive for sub-objects)
                             // For O(1) we assume exact match or need a Trie. 
                             // Given the requirements, we stick to exact match or flat set.
                             
                             // Simplification: logic here depends on "Recursive Pruning" vs "Exact Match".
                             // Let's assume strict set membership for now as per "Compile-to-Flat".
                             warn!("⚔️ [Immunity] Foreign antigen detected (Not in Allow Map): {}", param);
                             self.send_http_response(
                                403,
                                vec![("x-leukocyte-defense", "antigen-rejected")],
                                Some(b"Access Denied: Foreign Antigen"),
                             );
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
