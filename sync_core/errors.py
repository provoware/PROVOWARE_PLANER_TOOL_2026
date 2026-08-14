from __future__ import annotations


class SyncError(RuntimeError):
    pass


class SyncBaselineError(SyncError):
    pass


class SyncPlanBlockedError(SyncError):
    pass


class SyncStalePlanError(SyncError):
    pass


class SyncPostcheckError(SyncError):
    pass


class InjectedSyncFault(SyncError):
    pass
