import io
from typing import Dict, Optional, Union, Any, Tuple, List, Callable, Iterable

WSGIEnv = Dict[str, Any]  # Cannot use TypedDict because of 'HTTP_' variables
StartResponse = Callable[[str, List[Tuple[str, str]]], None]
WSGIApp = Callable[[WSGIEnv, StartResponse], Iterable[bytes]]


def create_wsgi_env(
    path: str,
    method: str,
    body: Union[str, bytes] = b"",
    queries: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    content_type: str = "text/plain; charset=utf-8",
) -> WSGIEnv:
    request_method = method.upper()
    bytes_body = body if isinstance(body, bytes) else body.encode("utf-8")
    wsgi_input = io.BytesIO(bytes_body)
    content_length = len(body)

    # 'key1=value1&key2=value2'
    query_string = "&".join([f"{k}={v}" for k, v in queries.items()]) if queries else ""

    # See https://www.python.org/dev/peps/pep-3333/#environ-variables
    env = {
        "PATH_INFO": path,
        "REQUEST_METHOD": request_method,
        "SCRIPT_NAME": "",
        "QUERY_STRING": query_string,
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": content_length,
        "SERVER_PROTOCOL": "http",
        "SERVER_NAME": "localhost",
        "wsgi.input": wsgi_input,
        "wsgi.version": (1, 0),
        "wsgi.errors": io.StringIO(""),
        "wsgi.multithread": True,
        "wsgi.multitprocess": True,
        "wsgi.run_once": False,
    }
    headers = headers or {}
    for k, v in headers.items():
        env[f"HTTP_{k.upper()}"] = v
    return env


def send_request(
    app: WSGIApp,
    path: str,
    method: str,
    body: Union[str, bytes] = b"",
    queries: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    content_type: str = "text/plain; charset=utf-8",
) -> Tuple[str, List[Tuple[str, str]], bytes]:
    status: str = ""
    response_headers: List[Tuple[str, str]] = []

    def start_response(status_: str, headers_: List[Tuple[str, str]]) -> None:
        nonlocal status, response_headers
        status = status_
        response_headers = headers_

    env = create_wsgi_env(path, method, body=body, queries=queries, headers=headers, content_type=content_type)
    body = b""
    iterable_body = app(env, start_response)
    for b in iterable_body:
        body += b

    return status, response_headers, body
