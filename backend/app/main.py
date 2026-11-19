"""Punto de composición de la API. Arranque desde backend con uvicorn app.main:app."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.schemas import ConsultaEntrada, PrediccionSalida, ReporteEntrada
from app.application.dashboard import DashboardService
from app.domain.contracts import Consulta
from app.infrastructure.motor import MotorLocal
from app.infrastructure.sqlite import SQLiteRegistro


def create_app(db_path: Path | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(api: FastAPI):
        motor = MotorLocal()
        database = db_path or Path(
            os.getenv("CAFESMART_DB", Path(__file__).resolve().parents[1] / "storage/cafesmart.db")
        )
        api.state.registro = SQLiteRegistro(database)
        api.state.motor = motor
        api.state.dashboard = DashboardService(motor, api.state.registro)
        yield

    api = FastAPI(title="CafeSmart AI", version="1.0.0", lifespan=lifespan)
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @api.exception_handler(ValueError)
    async def value_error(_request: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @api.exception_handler(Exception)
    async def server_error(_request: Request, exc: Exception):
        logging.exception("Error al procesar la solicitud", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "No pudimos completar la consulta. Revisa el registro del servidor."
            },
        )

    @api.get("/health")
    def health():
        return {"status": "ok"}

    @api.get("/api/catalogo")
    def catalogo(request: Request):
        return request.app.state.motor.catalogo()

    @api.post("/api/predecir", response_model=PrediccionSalida)
    def predecir(entrada: ConsultaEntrada, request: Request):
        consulta = Consulta(**entrada.model_dump(mode="json"))
        return request.app.state.dashboard.consultar(consulta)

    @api.get("/api/historial")
    def historial(request: Request):
        return request.app.state.registro.listar()

    @api.post("/api/reportes", status_code=201)
    def reportar(entrada: ReporteEntrada, request: Request):
        try:
            identificador = request.app.state.registro.reportar(
                entrada.consulta_id, entrada.comentario
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"id": identificador, "mensaje": "Reporte guardado."}

    return api


app = create_app()
