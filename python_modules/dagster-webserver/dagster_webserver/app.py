from typing import Optional

from dagster import _check as check
from dagster._core.execution.compute_logs import warn_if_compute_logs_disabled
from dagster._core.telemetry import log_workspace_stats
from dagster._core.workspace.context import IWorkspaceProcessContext
from starlette.applications import Starlette

from dagster_webserver.webserver import DagsterWebserver
from dagster_webserver.auth import create_auth_manager_from_instance_config


def create_app_from_workspace_process_context(
    workspace_process_context: IWorkspaceProcessContext,
    path_prefix: str = "",
    live_data_poll_rate: Optional[int] = None,
    **kwargs,
) -> Starlette:
    check.inst_param(
        workspace_process_context, "workspace_process_context", IWorkspaceProcessContext
    )
    check.str_param(path_prefix, "path_prefix")

    instance = workspace_process_context.instance

    if path_prefix:
        if not path_prefix.startswith("/"):
            raise Exception(f'The path prefix should begin with a leading "/": got {path_prefix}')
        if path_prefix.endswith("/"):
            raise Exception(f'The path prefix should not include a trailing "/": got {path_prefix}')

    warn_if_compute_logs_disabled()

    log_workspace_stats(instance, workspace_process_context)

    auth_manager = None
    try:
        if hasattr(instance, '_settings') and instance._settings:
            auth_storage_dir = instance.local_artifact_storage.base_dir + "/auth"
            auth_manager = create_auth_manager_from_instance_config(
                instance._settings,
                storage_dir=auth_storage_dir,
                base_url=path_prefix,
            )
    except Exception as e:
        import logging
        logging.getLogger("dagster.webserver").warning(
            f"Failed to initialize authentication manager: {e}. "
            "Continuing without authentication."
        )

    return DagsterWebserver(
        workspace_process_context,
        path_prefix,
        live_data_poll_rate,
        auth_manager=auth_manager,
    ).create_asgi_app(**kwargs)
