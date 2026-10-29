//! Unique identifier generation for SigmaOS components.
use std::sync::atomic::{AtomicU64, Ordering};

static COUNTER: AtomicU64 = AtomicU64::new(1);

/// A globally unique, monotonically increasing component ID.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ComponentId(u64);

impl ComponentId {
    pub fn generate() -> Self {
        ComponentId(COUNTER.fetch_add(1, Ordering::Relaxed))
    }
    pub fn as_u64(self) -> u64 { self.0 }
}

impl std::fmt::Display for ComponentId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "cid:{}", self.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ids_are_unique() {
        // Arrange / Act
        let a = ComponentId::generate();
        let b = ComponentId::generate();
        // Assert
        assert_ne!(a, b);
    }

    #[test]
    fn test_ids_are_monotonically_increasing() {
        // Arrange / Act
        let a = ComponentId::generate();
        let b = ComponentId::generate();
        // Assert
        assert!(b > a);
    }
}
