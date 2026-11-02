"""Print which stage started, which stage ended, and the completed and pending lists."""

from contextlib import contextmanager


class StageLog:
    def __init__(self, names: list[str]) -> None:
        # The full ordered list for this run. Pending is whatever is not done yet.
        self.names = list(names)
        self.done: list[str] = []
        self._report("PIPELINE STAGES")

    def _pending(self) -> list[str]:
        return [name for name in self.names if name not in self.done]

    def _names(self, names: list[str]) -> str:
        return ", ".join(names) if names else "none"

    def _report(self, headline: str) -> None:
        """One block: the event, then the completed stages, then the pending stages."""
        total = len(self.names)
        pending = self._pending()
        print(headline, flush=True)
        print(
            f"COMPLETED ({len(self.done)}/{total}): {self._names(self.done)}",
            flush=True,
        )
        print(
            f"PENDING ({len(pending)}/{total}): {self._names(pending)}",
            flush=True,
        )

    @contextmanager
    def stage(self, name: str):
        """Log the stage before the work, then again after it finishes or fails."""
        if name not in self.names:
            raise KeyError(f"Unknown stage: {name}")
        self._report(f"STAGE STARTED: {name}")
        try:
            yield
        except Exception as error:
            # This stage stays pending, along with every stage that has not run.
            self._report(f"STAGE FAILED: {name} | {error}")
            raise
        else:
            self.done.append(name)
            self._report(f"STAGE ENDED: {name}")
