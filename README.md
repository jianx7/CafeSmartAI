# CaféSmart AI

Aplicación local para estimar el menú de una cafetería según la sucursal, la fecha y el clima. Este proyecto contiene dos partes que corren al mismo tiempo, cada una en su terminal:

- **Backend** (`backend/`): API de FastAPI que ejecuta el modelo de la Entrega 3.
- **Frontend** (`frontend/`): interfaz en React que consulta a la API.

Todo lo necesario ya viene incluido: los datos y los modelos entrenados. Solo necesitas Internet para instalar las dependencias.

## Requisitos

| Programa | Versión | Cómo comprobarla (PowerShell) |
| --- | --- | --- |
| Python | 3.12 o 3.13 | `py --list` |
| Node.js | 22.12 o superior | `node --version` |
| VS Code | Cualquiera | Opcional, pero los pasos asumen que lo usas. |

## Paso a paso (Windows)

Haz estos pasos **en orden**. Usa dos terminales de PowerShell y no cierres ninguna mientras uses la app.


### Paso 1 · Instala y arranca el backend (Terminal 1)

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Si tienes Python 3.12, cambia `py -3.13` por `py -3.12`.
- Los tres primeros comandos se ejecutan solo la primera vez. Instalar tarda unos minutos.
- Debe aparecer `Uvicorn running on http://127.0.0.1:8000`. **Deja esta terminal abierta.**
- Comprueba que funciona: abre <http://127.0.0.1:8000/health>. Debe mostrar `{"status":"ok"}`.

### Paso 2 · Instala y arranca el frontend (Terminal 2)

Abre una segunda terminal con el botón **+** del panel de terminal. Debe iniciar en la carpeta raíz del proyecto.

```powershell
cd frontend
npm ci
npm run dev
```

- `npm ci` se ejecuta solo la primera vez.
- Debe aparecer una dirección local `http://127.0.0.1:5173`. **Deja esta terminal abierta.**

### Paso 3 · Abre la aplicación y comprueba que todo funciona

1. Abre <http://127.0.0.1:5173> en el navegador.
2. Pulsa **Cargar ejemplo**.
3. Debes ver **572.92 unidades** para Hell's Kitchen el 15 de junio de 2023. Con la franja 06:00–10:59, el total es **326.87**.

Si aparecen esos números, el frontend, el backend y el modelo están conectados.

### Para volver a usarla otro día

No repitas la instalación. En cada terminal ejecuta solo:

| Terminal | Comandos |
| --- | --- |
| 1 · Backend | `cd backend` y luego `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` |
| 2 · Frontend | `cd frontend` y luego `npm run dev` |

Para detener la aplicación, pulsa `Ctrl + C` en cada terminal.

## macOS o Linux

Es igual, con estos cambios en el Paso 2:

```bash
cd backend
python3.13 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

El Paso 2 usa los mismos comandos de npm.

## Si algo falla

| Qué ves | Causa y solución |
| --- | --- |
| `py` no se reconoce, o dice que no encuentra la versión | Instala Python 3.12 o 3.13 desde python.org con la opción del lanzador `py`. Cambia el número de versión en el comando. |
| `No module named 'app'` | Ejecutaste uvicorn fuera de `backend`. Haz `cd backend` y repite el comando. |
| `No module named 'fastapi'` u otro módulo | No se instalaron las dependencias o usaste otro Python. Repite el comando `pip install` del Paso 2 y arranca con `.\.venv\Scripts\python.exe`. |
| Error al cargar el modelo (`No module named '_loss'` o similar) | Hay otra versión de scikit-learn instalada. Los modelos requieren la 1.8.0. Borra la carpeta `backend\.venv` y repite el Paso 2. |
| `address already in use` en el puerto 8000 | Ya hay un backend abierto. Cierra la otra terminal con `Ctrl + C`. |
| Vite dice que el puerto 5173 está en uso | Ya hay un frontend abierto. Cierra la otra terminal con `Ctrl + C`. |
| `npm ci` falla con un aviso de versión de Node | Tu Node es anterior a 22.12. Instala una versión nueva. |
| La página abre, pero muestra un error al estimar | El backend no está corriendo. Revisa la Terminal 1 y pulsa **Reintentar**. |
| Error 422 o "fecha fuera de rango" | Solo se aceptan fechas del 26 de mayo al 30 de junio de 2023. |

## Qué hace cada sección de la interfaz

| Sección | Función |
| --- | --- |
| Inicio | Muestra unidades y ventas estimadas, categorías, clima, menú top 5, demanda por franja y tendencia histórica. |
| Recomendaciones | Lista los 13 tipos de producto y permite filtrar por categoría. Incluye el gráfico del top 5 y el nombre del modelo usado. |
| Ventas | Compara unidades reales y estimadas del periodo de prueba. Ofrece una tabla de valores. |
| Sucursales | Compara unidades reales del día completo de las tres sucursales. |
| Historial | Consulta las últimas 100 estimaciones guardadas en SQLite. |
| Configuración | Guarda la apariencia en el navegador y envía comentarios asociados a una consulta. |

Los filtros se aplican al pulsar **Estimar menú**. **Cargar ejemplo** restablece y ejecuta el caso de la Entrega 3. Puedes elegir día completo o una de las tres franjas, un periodo de 7, 14 o 30 días y, opcionalmente, un clima manual.

## Cómo se conectan las partes

React envía un JSON a `POST /api/predecir`. FastAPI lo valida, ejecuta `predecir()` con los modelos entrenados, guarda la consulta en SQLite y devuelve las cantidades, el menú y los datos de las gráficas. En desarrollo, Vite reenvía las solicitudes que empiezan con `/api` al puerto 8000.

## Datos y alcance

- Ventas de Astoria, Hell's Kitchen y Lower Manhattan, de enero a junio de 2023.
- La interfaz acepta fechas del conjunto de prueba, del 26 de mayo al 30 de junio de 2023.
- El clima viene del histórico ERA5 de Open-Meteo. Las tres sucursales comparten la misma serie.
- Las ventas estimadas usan precios medios en USD calculados con el conjunto de entrenamiento.
- Cada barra horaria usa el modelo por franja. El total del día usa el modelo diario, por lo que sus cifras pueden diferir.
- Las clasificaciones Alta, Media y Baja comparan con las unidades medias de los siete días previos.
- La selección de modelos es la de validación de la Entrega 3.

Para pronosticar fechas actuales hace falta actualizar las ventas, generar las variables de los siete días previos y usar un pronóstico meteorológico disponible antes del turno. Esta versión evalúa casos históricos.

## Pruebas (opcional)

Frontend, desde `frontend`:

```powershell
npm test
npm run build
```

Backend, desde `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Configuración avanzada (opcional)

| Variable | Dónde se usa | Valor por defecto |
| --- | --- | --- |
| `VITE_API_URL` | `frontend/.env` | `/api` |
| `CORS_ORIGINS` | Entorno del backend, orígenes separados por coma | `http://localhost:5173,http://127.0.0.1:5173` |
| `CAFESMART_DB` | Entorno del backend, ubicación de SQLite | `backend/storage/cafesmart.db` |
