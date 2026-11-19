# CafeSmart AI - Modelo

> Este archivo es solo para volver a entrenar el modelo. Para ejecutar la aplicación, sigue el README de la raíz del proyecto. No necesitas nada de lo que sigue.

El proyecto entrena dos regresores de unidades vendidas y convierte sus estimaciones en un menú de cinco tipos de producto. La corrida diaria reproduce la Entrega 2. La corrida por franjas conserva el objetivo de recomendar un menú para distintos horarios.

## 1. Abre la carpeta y prepara Python

Descomprime el ZIP y abre en VS Code la carpeta que contiene este README. Abre una terminal de PowerShell y ejecuta estos comandos con Python 3.13 instalado. También puedes usar Python 3.12 cambiando el selector de versión.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En macOS o Linux, crea el entorno con `python3.13 -m venv .venv` y usa `./.venv/bin/python` en lugar de `.\.venv\Scripts\python.exe`.

## 2. Ejecuta el notebook en VS Code

1. Instala las extensiones Python y Jupyter de VS Code.
2. Abre `notebooks/03_model_training.ipynb` y elige **Seleccionar kernel → Entornos de Python → .venv**.
3. Pulsa **Run All / Ejecutar todo**. El notebook prepara los datos, entrena los dos experimentos y muestra las métricas, las dos curvas de MAE y un ejemplo de recomendación. Cada ejecución vuelve a generar los modelos y las métricas.

El notebook llama a `src/data/preprocess.py` y `src/models/train.py`. La sección de terminal permite ejecutar esas mismas etapas por separado.

## 3. Entiende y verifica los datos

- El CSV de ventas original está en `data/raw/Coffee_Shop_Sales.csv`. El campo `transaction_qty` contiene las unidades.
- El clima de Nueva York ya viene descargado en `data/raw/clima_nyc_2023.csv`. Puedes regenerarlo con el siguiente comando. Solo este paso requiere acceso a Open-Meteo.
- El archivo JSON junto al clima registra las consultas y coordenadas devueltas. Las tres sucursales quedaron en la misma celda ERA5 y comparten la serie meteorológica. Las coordenadas solicitadas aproximan los barrios porque el CSV no contiene domicilios.

```powershell
.\.venv\Scripts\python.exe -m src.data.clima
```

El script usa la API histórica de Open-Meteo, las fechas del CSV de ventas y la zona horaria America/New_York. Pide temperatura y humedad por hora y promedia cada día local. Para lluvia usa el acumulado diario `rain_sum`, en milímetros. Une el clima a las ventas por fecha y sucursal. Fuente: [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api).

## 4. Ejecuta el entrenamiento desde la terminal

Desde la raíz del proyecto, ejecuta primero la comparación diaria.

```powershell
.\.venv\Scripts\python.exe -m src.data.preprocess --clima data/raw/clima_nyc_2023.csv
.\.venv\Scripts\python.exe -m src.models.train --data data/processed/ventas_diarias_por_producto.csv
```

El primer comando filtra Coffee, Tea, Drinking Chocolate y Bakery. Agrupa por fecha, sucursal y tipo. El promedio de siete días y el lag se calculan con ventas anteriores a cada fecha. El segundo comando crea dos referencias simples y ajusta Random Forest y Gradient Boosting. Usa tres cortes dentro de entrenamiento y evalúa las variantes con y sin clima en las mismas fechas de prueba. Los modelos y el codificador de categorías se guardan juntos como pipelines en `models/`.

Las franjas elegidas para cubrir el horario del CSV son **06:00–10:59**, **11:00–14:59** y **15:00–20:59**. Para reproducir este experimento separado:

```powershell
.\.venv\Scripts\python.exe -m src.data.preprocess --clima data/raw/clima_nyc_2023.csv --por-franja --output data/processed/ventas_por_franja.csv
.\.venv\Scripts\python.exe -m src.models.train --data data/processed/ventas_por_franja.csv --output models/franjas --evidencias evidencias/franjas
```

## 5. Ejecuta una predicción

```powershell
.\.venv\Scripts\python.exe -m src.models.predict
.\.venv\Scripts\python.exe -m src.models.predict --franja "06:00–10:59"
```

Ambos comandos usan Hell's Kitchen y el 15 de junio de 2023. Para cambiar el ejemplo, usa `--sucursal "Astoria" --fecha 2023-06-20`. El backend de la aplicación ya importa `predecir` desde `src.models.predict`. Recibe un diccionario con `sucursal`, `fecha`, `franja` opcional y `clima` opcional. Solo admite el rango histórico de la demo y requiere siete días de ventas previas. La evaluación es retrospectiva: un pronóstico real antes de abrir necesitaría clima disponible a esa hora y una fuente actualizada de ventas.

## 6. Ubica las evidencias

| Archivo o carpeta | Qué contiene |
| --- | --- |
| `evidencias/entrenamiento.txt` | Registro real de la corrida diaria |
| `evidencias/metricas.csv` | MAE de entrenamiento, validación y prueba, acierto top 5 y tiempos |
| `evidencias/ajuste.csv` | Hiperparámetros probados y MAE de validación |
| `evidencias/curva_mae.png` | Curva de entrenamiento y validación de Gradient Boosting |
| `evidencias/inferencia_diaria.json` | Entrada y salida de la demo diaria |
| `evidencias/franjas/` | Métricas, registro y gráfica del experimento por franja |
| `models/seleccion.json` | Candidato elegido por validación interna, antes de consultar el resultado de prueba |

El MAE mide cuántas unidades se desvía la predicción en promedio por fila. El acierto del menú cuenta cuántos de los cinco tipos recomendados aparecen en los cinco más vendidos del mismo grupo. Los empates se resuelven por el nombre del tipo. El promedio móvil usa ventas reales disponibles hasta el día anterior, también durante la prueba. Los tiempos varían según el equipo.

La comparación entre candidatos de IA y la comparación con las reglas simples cumplen funciones distintas. El reporte indica cuál candidato se eligió por validación, cuál tuvo menor error de prueba y si superó la referencia móvil.
