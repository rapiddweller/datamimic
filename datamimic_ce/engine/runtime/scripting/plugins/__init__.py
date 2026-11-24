"""Runtime-owned execution of user-provided script plugins."""

# The module name of every class a script defines: the runtime tells such a class from an engine or library class.
SCRIPT_MODULE = __name__


def execute_script(source: str, namespace: dict[str, object]) -> None:
    """Execute a setup script in the supplied namespace, preserving Python's globals/locals rules."""
    # A loaded module, not "builtins" or "__main__": @dataclass execs into sys.modules[cls.__module__].__dict__.
    namespace.setdefault("__name__", SCRIPT_MODULE)
    # dont_inherit: a script must not receive the future flags of this module.
    exec(compile(source, "<string>", "exec", dont_inherit=True), namespace)


__all__ = ["SCRIPT_MODULE", "execute_script"]
