"""Persistencia local con conexiones por operación y transacciones de SQLite."""

from contextlib import contextmanager
from dataclasses import asdict
import json
import sqlite3
from pathlib import Path

from app.domain.contracts import Consulta


class SQLiteRegistro:
    def __init__(self, archivo: Path):
        archivo.parent.mkdir(parents=True, exist_ok=True)
        self.archivo = archivo
        with self.conectar() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS consultas (
                    id INTEGER PRIMARY KEY,
                    creada TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    entrada TEXT NOT NULL,
                    salida TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reportes (
                    id INTEGER PRIMARY KEY,
                    consulta_id INTEGER NOT NULL REFERENCES consultas(id),
                    comentario TEXT NOT NULL,
                    creado TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                );
            """)

    @contextmanager
    def conectar(self):
        conexion = sqlite3.connect(self.archivo, timeout=10)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        try:
            with conexion:
                yield conexion
        finally:
            conexion.close()

    def guardar_consulta(self, consulta: Consulta, resultado: dict) -> int:
        with self.conectar() as conn:
            cursor = conn.execute(
                "INSERT INTO consultas(entrada, salida) VALUES (?, ?)",
                (json.dumps(asdict(consulta)), json.dumps(resultado, allow_nan=False)),
            )
            return int(cursor.lastrowid)

    def listar(self) -> list[dict]:
        with self.conectar() as conn:
            filas = conn.execute("SELECT * FROM consultas ORDER BY id DESC LIMIT 100").fetchall()
        return [
            {
                "id": fila["id"],
                "creada": fila["creada"],
                "entrada": json.loads(fila["entrada"]),
                "prediccion": json.loads(fila["salida"])["prediccion"],
            }
            for fila in filas
        ]

    def reportar(self, consulta_id: int, comentario: str) -> int:
        with self.conectar() as conn:
            if (
                conn.execute("SELECT 1 FROM consultas WHERE id = ?", (consulta_id,)).fetchone()
                is None
            ):
                raise LookupError("La consulta no existe.")
            cursor = conn.execute(
                "INSERT INTO reportes(consulta_id, comentario) VALUES (?, ?)",
                (consulta_id, comentario),
            )
            return int(cursor.lastrowid)
