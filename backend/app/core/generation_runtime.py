"""Runtime guard for approved on-demand generation workers."""

LOCAL_WORKER_ENVS = {"local", "dev", "development"}


def ensure_generation_worker_allowed(
    env: str,
    confirmed: bool,
    *,
    production_enabled: bool,
) -> None:
    """Allow generation writes only with an explicit runtime gate."""
    if not confirmed:
        raise RuntimeError("Refusing generation worker writes without --confirm-generation-write.")
    normalized = env.strip().lower()
    if normalized in LOCAL_WORKER_ENVS:
        return
    if normalized == "production" and production_enabled:
        return
    raise RuntimeError(
        f"Refusing generation worker writes when ENV={env!r}. "
        "Production requires AI_GENERATION_WORKERS_ENABLED=true."
    )
