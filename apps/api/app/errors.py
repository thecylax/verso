from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.security import clear_session_cookie

FIELD_LABELS = {
    "name": "nome",
    "email": "e-mail",
    "password": "senha",
    "title": "título",
    "content_md": "conteúdo",
    "folder_id": "pasta",
    "parent_id": "pasta",
    "bible_version": "versão bíblica",
    "id": "identificador",
}


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, clear_cookie: bool = False):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.clear_cookie = clear_cookie


def unauthorized(message: str = "Sessão ausente ou expirada.", clear_cookie: bool = False) -> ApiError:
    return ApiError(401, "unauthorized", message, clear_cookie)


def not_found(message: str = "Recurso não encontrado.") -> ApiError:
    return ApiError(404, "not_found", message)


def conflict(message: str) -> ApiError:
    return ApiError(409, "conflict", message)


def validation_error(message: str) -> ApiError:
    return ApiError(422, "validation_error", message)


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def _validation_message(error: dict) -> str:
    loc = [part for part in error.get("loc", ()) if part not in ("body", "query", "path")]
    field = FIELD_LABELS.get(str(loc[-1]), str(loc[-1])) if loc else ""
    kind = error.get("type", "")
    if kind == "value_error":
        message = str(error.get("msg", ""))
        return message.removeprefix("Value error, ")
    if kind == "missing":
        return f"O campo {field} é obrigatório." if field else "Corpo da requisição ausente."
    if kind == "json_invalid":
        return "Corpo JSON inválido."
    if kind == "uuid_parsing" or kind == "uuid_type":
        return f"Identificador inválido em {field}." if field else "Identificador inválido."
    if field:
        return f"O campo {field} tem formato inválido."
    return "Requisição inválida."


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
        response = JSONResponse(error_body(exc.code, exc.message), status_code=exc.status)
        if exc.clear_cookie:
            clear_session_cookie(response)
        return response

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        message = _validation_message(errors[0]) if errors else "Requisição inválida."
        return JSONResponse(error_body("validation_error", message), status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return JSONResponse(error_body("not_found", "Recurso não encontrado."), status_code=404)
        if exc.status_code == 401:
            return JSONResponse(error_body("unauthorized", "Sessão ausente ou expirada."), status_code=401)
        return JSONResponse(error_body("http_error", str(exc.detail)), status_code=exc.status_code)
