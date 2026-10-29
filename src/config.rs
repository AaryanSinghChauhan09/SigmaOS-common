//! Key-value configuration store for SigmaOS components.
use std::collections::HashMap;

/// A simple typed configuration bag — Information Hiding, Command-Query Separation.
#[derive(Debug, Default, Clone)]
pub struct Config {
    store: HashMap<String, String>,
}

impl Config {
    pub fn new() -> Self { Self::default() }

    // ── Queries ──────────────────────────────────────────────────────────
    pub fn get(&self, key: &str) -> Option<&str> {
        self.store.get(key).map(|s| s.as_str())
    }
    pub fn get_or(&self, key: &str, default: &str) -> String {
        self.store.get(key).cloned().unwrap_or_else(|| default.to_string())
    }
    pub fn contains(&self, key: &str) -> bool { self.store.contains_key(key) }
    pub fn len(&self) -> usize { self.store.len() }
    pub fn is_empty(&self) -> bool { self.store.is_empty() }

    // ── Commands ─────────────────────────────────────────────────────────
    pub fn set(&mut self, key: impl Into<String>, value: impl Into<String>) {
        self.store.insert(key.into(), value.into());
    }
    pub fn remove(&mut self, key: &str) -> Option<String> { self.store.remove(key) }
    pub fn clear(&mut self) { self.store.clear(); }

    pub fn merge(&mut self, other: &Config) {
        for (k, v) in &other.store {
            self.store.entry(k.clone()).or_insert_with(|| v.clone());
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_set_and_get() {
        // Arrange
        let mut c = Config::new();
        // Act
        c.set("theme", "dark");
        // Assert
        assert_eq!(c.get("theme"), Some("dark"));
    }

    #[test]
    fn test_missing_key_returns_none() {
        // Arrange
        let c = Config::new();
        // Assert
        assert_eq!(c.get("nonexistent"), None);
    }

    #[test]
    fn test_get_or_uses_default() {
        // Arrange
        let c = Config::new();
        // Assert
        assert_eq!(c.get_or("lang", "en"), "en");
    }

    #[test]
    fn test_merge_does_not_overwrite() {
        // Arrange
        let mut base = Config::new();
        base.set("k", "original");
        let mut overlay = Config::new();
        overlay.set("k", "override");
        overlay.set("new", "value");
        // Act
        base.merge(&overlay);
        // Assert
        assert_eq!(base.get("k"), Some("original")); // not overwritten
        assert_eq!(base.get("new"), Some("value"));  // new key added
    }

    #[test]
    fn test_remove() {
        // Arrange
        let mut c = Config::new();
        c.set("x", "1");
        // Act
        let removed = c.remove("x");
        // Assert
        assert_eq!(removed, Some("1".to_string()));
        assert!(!c.contains("x"));
    }
}
