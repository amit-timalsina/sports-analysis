"""FastAPI provider for the dependency injection container."""

from collections.abc import AsyncGenerator
from typing import Annotated

import svcs
from fastapi import Depends, Request, WebSocket


async def container(
    request: Request | None = None,
    websocket: WebSocket | None = None,
) -> AsyncGenerator[svcs.Container, None]:
    """Yield a dependency injection container for the current request."""
    if request is None and websocket is None:
        msg = "Either request or websocket must be provided"
        raise ValueError(msg)
    if request is not None:
        state = request.state
    elif websocket is not None:
        state = websocket.state
    else:
        msg = "Unexpected state: both request and websocket are None"
        raise ValueError(msg)
    registry = getattr(state, svcs._core._KEY_REGISTRY)  # noqa: SLF001
    async with svcs.Container(registry) as container:
        yield container


DepContainer = Annotated[svcs.Container, Depends(container)]
