"""Stabile Fehlerklassen des Kalender-Datenkerns."""


class CalendarError(Exception):
    """Basisklasse für erwartbare Kalenderfehler."""


class DomainValidationError(CalendarError):
    pass


class EventNotFoundError(CalendarError):
    pass


class ConcurrentUpdateError(CalendarError):
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


class RestoreRejectedError(BackupError):
    pass
