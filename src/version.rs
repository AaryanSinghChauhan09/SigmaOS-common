//! Semantic versioning for SigmaOS components.
use std::fmt;
use std::str::FromStr;

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct Version { pub major: u32, pub minor: u32, pub patch: u32 }

#[derive(Debug)]
pub struct ParseVersionError(String);

impl fmt::Display for ParseVersionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "invalid version string: {}", self.0)
    }
}

impl Version {
    pub const fn new(major: u32, minor: u32, patch: u32) -> Self {
        Self { major, minor, patch }
    }
    pub fn is_compatible_with(&self, other: &Version) -> bool {
        self.major == other.major && self.minor >= other.minor
    }
}

impl fmt::Display for Version {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}.{}.{}", self.major, self.minor, self.patch)
    }
}

impl FromStr for Version {
    type Err = ParseVersionError;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let parts: Vec<&str> = s.trim().split('.').collect();
        if parts.len() != 3 {
            return Err(ParseVersionError(s.to_string()));
        }
        let parse = |p: &str| p.parse::<u32>().map_err(|_| ParseVersionError(s.to_string()));
        Ok(Self::new(parse(parts[0])?, parse(parts[1])?, parse(parts[2])?))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version_ordering() {
        // Arrange
        let v1 = Version::new(1, 2, 3);
        let v2 = Version::new(1, 3, 0);
        // Assert
        assert!(v1 < v2);
    }

    #[test]
    fn test_parse_valid_version() {
        // Arrange / Act
        let v: Version = "2.5.1".parse().unwrap();
        // Assert
        assert_eq!(v, Version::new(2, 5, 1));
    }

    #[test]
    fn test_parse_invalid_version_returns_error() {
        // Arrange / Act
        let result = "bad".parse::<Version>();
        // Assert
        assert!(result.is_err());
    }

    #[test]
    fn test_compatibility_same_major() {
        // Arrange
        let base = Version::new(2, 0, 0);
        let compat = Version::new(2, 1, 0);
        let incompat = Version::new(3, 0, 0);
        // Assert
        assert!(compat.is_compatible_with(&base));
        assert!(!incompat.is_compatible_with(&base));
    }

    #[test]
    fn test_display_format() {
        // Arrange
        let v = Version::new(1, 0, 7);
        // Assert
        assert_eq!(v.to_string(), "1.0.7");
    }
}
