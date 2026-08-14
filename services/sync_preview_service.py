from __future__ import annotations

from sync_core.model import SyncFieldAction, SyncFieldPreview, SyncPreview, SyncPreviewState
from services.calendar_service import CalendarService
from services.todo_service import TodoCalendarLinkService, TodoService
from todo_core.model import LinkConflictStatus, LinkDirection


class SynchronizationPreviewService:
    """Erzeugt ausschließlich eine Vorschau. Diese Klasse besitzt absichtlich keine Schreib-API."""

    def __init__(
        self,
        todos: TodoService,
        calendar: CalendarService,
        links: TodoCalendarLinkService,
    ) -> None:
        self.todos = todos
        self.calendar = calendar
        self.links = links

    def preview(self, link_id: str) -> SyncPreview:
        link = self.links.get_link(link_id)
        todo = self.todos.get_todo(link.todo_id, include_deleted=True)
        event = self.calendar.get_event(link.event_id, include_deleted=True)
        conflict = self.links.preview_conflict(link_id)

        fields = (
            self._field("TITLE", "title", "title", todo.title, event.title, conflict, link.direction, automatic=True),
            self._field(
                "DESCRIPTION",
                "description",
                "description",
                todo.description,
                event.description,
                conflict,
                link.direction,
                automatic=True,
            ),
            self._field(
                "START_AT",
                "start_at",
                "start_at",
                todo.start_at,
                event.start_at,
                conflict,
                link.direction,
                automatic=True,
            ),
            self._field(
                "DUE_END",
                "due_at",
                "end_at",
                todo.due_at,
                event.end_at,
                conflict,
                link.direction,
                automatic=False,
                semantic_review=True,
            ),
        )
        state, reason = self._state(conflict, link.direction, fields)
        return SyncPreview(
            link_id=link.link_id,
            state=state,
            conflict_status=conflict,
            direction=link.direction,
            todo_version=todo.version,
            calendar_version=event.version,
            todo_version_at_sync=link.todo_version_at_sync,
            calendar_version_at_sync=link.event_version_at_sync,
            fields=fields,
            write_permitted=False,
            blocking_reason=reason,
        )

    @staticmethod
    def _field(
        field_id: str,
        todo_field: str,
        calendar_field: str,
        todo_value: object,
        calendar_value: object,
        conflict: LinkConflictStatus,
        direction: LinkDirection,
        *,
        automatic: bool,
        semantic_review: bool = False,
    ) -> SyncFieldPreview:
        if todo_value == calendar_value:
            return SyncFieldPreview(
                field_id, todo_field, calendar_field, todo_value, calendar_value,
                SyncFieldAction.IDENTISCH, "Beide Seiten enthalten denselben Wert.", False,
            )
        if conflict is LinkConflictStatus.DETACHED:
            return SyncFieldPreview(
                field_id, todo_field, calendar_field, todo_value, calendar_value,
                SyncFieldAction.BLOCKIERT, "Mindestens ein Endpunkt wurde fachlich gelöscht oder getrennt.", False,
            )
        if conflict is LinkConflictStatus.BOTH_CHANGED:
            return SyncFieldPreview(
                field_id, todo_field, calendar_field, todo_value, calendar_value,
                SyncFieldAction.BLOCKIERT, "Beide Objekte wurden seit dem letzten Snapshot geändert.", False,
            )
        if conflict is LinkConflictStatus.CLEAN:
            return SyncFieldPreview(
                field_id, todo_field, calendar_field, todo_value, calendar_value,
                SyncFieldAction.BLOCKIERT,
                "Die Werte unterscheiden sich bereits ohne neue Versionsänderung; eine sichere Ausgangsbasis fehlt.",
                False,
            )
        if semantic_review:
            return SyncFieldPreview(
                field_id, todo_field, calendar_field, todo_value, calendar_value,
                SyncFieldAction.PRUEFUNG_ERFORDERLICH,
                "Fälligkeit und Terminende sind semantisch nicht automatisch gleichzusetzen.",
                False,
            )
        if conflict is LinkConflictStatus.TODO_CHANGED:
            if direction in {LinkDirection.TODO_TO_CALENDAR, LinkDirection.BIDIRECTIONAL}:
                return SyncFieldPreview(
                    field_id, todo_field, calendar_field, todo_value, calendar_value,
                    SyncFieldAction.TODO_ZU_KALENDER,
                    "Nur die Aufgabe wurde seit dem Snapshot geändert und die Richtung erlaubt Todo→Kalender.",
                    automatic,
                )
            return SyncFieldPreview(
                field_id, todo_field, calendar_field, todo_value, calendar_value,
                SyncFieldAction.BLOCKIERT, "Die Link-Richtung erlaubt Todo→Kalender nicht.", False,
            )
        if conflict is LinkConflictStatus.CALENDAR_CHANGED:
            if direction in {LinkDirection.CALENDAR_TO_TODO, LinkDirection.BIDIRECTIONAL}:
                return SyncFieldPreview(
                    field_id, todo_field, calendar_field, todo_value, calendar_value,
                    SyncFieldAction.KALENDER_ZU_TODO,
                    "Nur der Termin wurde seit dem Snapshot geändert und die Richtung erlaubt Kalender→Todo.",
                    automatic,
                )
            return SyncFieldPreview(
                field_id, todo_field, calendar_field, todo_value, calendar_value,
                SyncFieldAction.BLOCKIERT, "Die Link-Richtung erlaubt Kalender→Todo nicht.", False,
            )
        return SyncFieldPreview(
            field_id, todo_field, calendar_field, todo_value, calendar_value,
            SyncFieldAction.BLOCKIERT, "Für diesen Zustand existiert keine sichere Regel.", False,
        )

    @staticmethod
    def _state(
        conflict: LinkConflictStatus,
        direction: LinkDirection,
        fields: tuple[SyncFieldPreview, ...],
    ) -> tuple[SyncPreviewState, str]:
        if conflict is LinkConflictStatus.DETACHED:
            return SyncPreviewState.BLOCKIERT_GETRENNT, "Getrennter oder gelöschter Endpunkt."
        if conflict is LinkConflictStatus.BOTH_CHANGED:
            return SyncPreviewState.BLOCKIERT_BEIDSEITIG, "BOTH_CHANGED wird in I008 niemals automatisch aufgelöst."
        differences = [field for field in fields if field.action is not SyncFieldAction.IDENTISCH]
        if not differences:
            return SyncPreviewState.KEINE_AENDERUNG, "Keine Feldabweichung vorhanden."
        if conflict is LinkConflictStatus.CLEAN:
            return SyncPreviewState.BLOCKIERT_BASISABWEICHUNG, "Abweichende Ausgangswerte ohne belastbare Feld-Baseline."
        if direction is LinkDirection.MANUAL:
            return SyncPreviewState.BLOCKIERT_RICHTUNG, "Manuelle Link-Richtung erlaubt keinen automatischen Vorschlag."
        if any(field.action is SyncFieldAction.PRUEFUNG_ERFORDERLICH for field in differences):
            return SyncPreviewState.MANUELLE_PRUEFUNG, "Mindestens ein Feld benötigt semantische Prüfung."
        if any(field.action is SyncFieldAction.BLOCKIERT for field in differences):
            return SyncPreviewState.BLOCKIERT_RICHTUNG, "Mindestens ein Feld ist durch Richtung oder Sicherheitsregel blockiert."
        return SyncPreviewState.VORSCHLAG_BEREIT, "Gerichteter Vorschlag ist berechnet; Schreiben bleibt in I008 gesperrt."
