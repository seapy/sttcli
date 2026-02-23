from contextlib import contextmanager

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn


@contextmanager
def make_progress():
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        transient=True,
        console=Console(stderr=True),
    )
    with progress:
        yield progress


class StepProgress:
    def __init__(self, progress: Progress, description: str, total: int = 100):
        self.progress = progress
        self.task_id = progress.add_task(description, total=total)

    def update(self, completed: int, description: str | None = None):
        kwargs = {"completed": completed}
        if description is not None:
            kwargs["description"] = description
        self.progress.update(self.task_id, **kwargs)

    def advance_to(self, pct: int, description: str | None = None):
        self.update(pct, description)
