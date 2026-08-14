class TodoError(Exception):
    """Basisfehler des Todo-Domainkerns."""


class TodoValidationError(TodoError, ValueError):
    pass


class TodoNotFoundError(TodoError):
    pass


class TodoConcurrentUpdateError(TodoError):
    pass


class TodoLinkError(TodoError):
    pass


class TodoLinkNotFoundError(TodoLinkError):
    pass


class TodoLinkConflictError(TodoLinkError):
    pass


class InjectedTodoFault(TodoError):
    pass
