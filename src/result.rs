//! Unified Result/Error type for SigmaOS components.
use std::fmt;

#[derive(Debug)]
pub enum SigmaError {
    NotFound(String),
    PermissionDenied(String),
    InvalidInput(String),
    Io(std::io::Error),
    Other(String),
}

impl fmt::Display for SigmaError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SigmaError::NotFound(s)        => write!(f, "not found: {s}"),
            SigmaError::PermissionDenied(s)=> write!(f, "permission denied: {s}"),
            SigmaError::InvalidInput(s)    => write!(f, "invalid input: {s}"),
            SigmaError::Io(e)              => write!(f, "io error: {e}"),
            SigmaError::Other(s)           => write!(f, "error: {s}"),
        }
    }
}

impl From<std::io::Error> for SigmaError {
    fn from(e: std::io::Error) -> Self { SigmaError::Io(e) }
}

pub type SigmaResult<T> = Result<T, SigmaError>;
