"""Opt-in bootstrap inherited by the service job's spawned Python workers."""

import os

if os.environ.get("MONGO_DIAGNOSTICS_DIR"):
    from mongo_diagnostics import install_monitoring

    install_monitoring()
