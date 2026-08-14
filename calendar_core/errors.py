class CalendarError(Exception):
    """Basisfehler des Kalenderkerns."""


class DomainValidationError(CalendarError, ValueError):
    pass


class DatabaseBusyError(CalendarError):
    pass


class DatabaseIntegrityError(CalendarError):
    pass


class MigrationError(CalendarError):
    pass


class MigrationTamperedError(MigrationError):
    pass


class BackupError(CalendarError):
    pass


class RestoreRejectedError(CalendarError):
    pass


class EventNotFoundError(CalendarError):
    pass


class MarkerNotFoundError(CalendarError):
    pass


class ConcurrentUpdateError(CalendarError):
    pass
