"""Custom exceptions for VibeCraft."""


class VibeCraftError(Exception):
    """Base exception for VibeCraft."""
    pass


class SongNotFoundError(VibeCraftError):
    """Song not found."""
    pass


class ClipNotFoundError(VibeCraftError):
    """Clip not found."""
    pass


class AnalysisError(VibeCraftError):
    """Analysis-related error."""
    pass


class AnalysisNotFoundError(AnalysisError):
    """Analysis not found."""
    pass


class ClipGenerationError(VibeCraftError):
    """Clip generation error."""
    pass


class ClipPlanningError(VibeCraftError):
    """Clip planning error."""
    pass


class CompositionError(VibeCraftError):
    """Composition error."""
    pass


class StorageError(VibeCraftError):
    """Storage operation error."""
    pass


class JobNotFoundError(VibeCraftError):
    """Job not found."""
    pass


class JobStateError(VibeCraftError):
    """Job is in an invalid state for the requested operation."""
    pass

