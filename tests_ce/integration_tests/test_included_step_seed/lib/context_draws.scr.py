class ContextDraws:
    """A library generator that draws from the stream of the context it gets."""

    def __init__(self, context):
        self._rng = context.root.derive_seeded_rng()

    def generate(self):
        return self._rng.randint(0, 999999999)
