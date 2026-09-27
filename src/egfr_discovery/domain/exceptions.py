class ModelValidationFailed(RuntimeError):

    def __init__(self, failures: tuple[str, ...]) -> None:

        message = "; ".join(failures)

        super().__init__(
            f"Model validation failed: {message}"
        )

        self.failures = failures