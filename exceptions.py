class Impossible(Exception):
    """Exception raised when an action is impossible to be performed.

    The reason should be given in the message.
    """


class QuitWithoutSaving(SystemExit):
    """Can be raised to exit the game without automatically saving."""
