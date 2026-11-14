class CtxGen:
    """A generator that draws through the context it receives."""

    def __init__(self, context):
        self.context = context

    def generate(self):
        return self.context.rng.randint(0, 999999999)
