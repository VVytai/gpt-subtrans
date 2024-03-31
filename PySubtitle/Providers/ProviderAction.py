class ProviderAction:
    def __init__(self, callback):
        self.callback = callback

    def __call__(self, *args, **kwargs):
        return self.callback(*args, **kwargs)
