"""Custom exceptions for searchlense."""

from __future__ import annotations


class SearchlenseError(Exception):
    """Base class for all searchlense errors."""


class ProviderError(SearchlenseError):
    """Raised when a SearchProvider fails to produce results."""


class LedgerError(SearchlenseError):
    """Raised when the ledger is used incorrectly."""


class ControllerError(SearchlenseError):
    """Raised when the playback controller is in an invalid state."""


class ControlError(SearchlenseError):
    """Raised when the control signal is misused."""


class RendererError(SearchlenseError):
    """Raised when a renderer fails."""


class SessionError(SearchlenseError):
    """Raised when a session is misconfigured or misused."""


class BridgeError(SearchlenseError):
    """Raised when the stdio bridge encounters a protocol error."""
