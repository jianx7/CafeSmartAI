"""Pruebas de integración con los modelos reales y una base de datos temporal."""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


class ApiIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.database = Path(cls.temporary.name) / "test.db"
        cls.context = TestClient(create_app(cls.database))
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)
        cls.temporary.cleanup()

    def test_catalog_and_real_daily_inference(self):
        catalog = self.client.get("/api/catalogo").json()
        self.assertEqual(len(catalog["sucursales"]), 3)
        response = self.client.post("/api/predecir", json=catalog["ejemplo"])
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["prediccion"], 572.92)
        self.assertEqual(len(data["productos"]), 13)
        self.assertEqual(data["menu_top5"][0]["producto"], "Barista Espresso")
        self.assertEqual(data["productos"][:5], data["menu_top5"])
        self.assertAlmostEqual(
            sum(p["unidades"] for p in data["productos"]), data["prediccion"], delta=0.1
        )
        self.assertAlmostEqual(
            sum(c["unidades"] for c in data["categorias"]), data["prediccion"], delta=0.1
        )
        self.assertEqual(len(data["tendencia"]), 7)
        self.assertEqual(data["sucursal"], "Hell's Kitchen")
        self.assertEqual(data["fuente_clima"], "historico")

    def test_time_band_and_manual_weather(self):
        payload = {"sucursal": "Hell's Kitchen", "fecha": "2023-06-15", "franja": "06:00–10:59"}
        response = self.client.post("/api/predecir", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["prediccion"], 326.87)
        self.assertEqual(response.json()["modelo"], "random_forest_con_clima")
        payload["clima"] = {"temperatura_c": 10, "humedad_pct": 80, "lluvia_mm": 5}
        manual = self.client.post("/api/predecir", json=payload)
        self.assertEqual(manual.status_code, 200, manual.text)
        self.assertEqual(manual.json()["fuente_clima"], "entrada")
        self.assertEqual(manual.json()["clima"], payload["clima"])
        self.assertNotEqual(manual.json()["prediccion"], response.json()["prediccion"])

    def test_invalid_inputs_do_not_create_history(self):
        initial = len(self.client.get("/api/historial").json())
        example = {"sucursal": "Astoria", "fecha": "2023-06-15"}
        for changes in [
            {"sucursal": "Centro"},
            {"fecha": "2028-01-01"},
            {"franja": "Noche"},
            {"periodo": 100},
            {"clima": {"temperatura_c": 20, "humedad_pct": 60, "lluvia_mm": -1}},
        ]:
            response = self.client.post("/api/predecir", json={**example, **changes})
            self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(len(self.client.get("/api/historial").json()), initial)

    def test_future_date_runs_as_scenario(self):
        payload = {"sucursal": "Hell's Kitchen", "fecha": "2026-11-19"}
        response = self.client.post("/api/predecir", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["modo"], "escenario")
        self.assertEqual(data["base_ventas"], {"desde": "2023-06-24", "hasta": "2023-06-30"})
        self.assertEqual(data["fecha"], "2026-11-19")
        self.assertEqual(len(data["productos"]), 13)
        self.assertGreater(data["prediccion"], 0)
        self.assertIsNone(data["clima"])
        self.assertIsNone(data["fuente_clima"])
        self.assertEqual(data["modelo"], "gradient_boosting_sin_clima")
        self.assertEqual(data["tendencia"], [])
        self.assertEqual(len(data["sucursales"]), 3)
        self.assertTrue(all(s["unidades_reales"] is None for s in data["sucursales"]))
        manual = self.client.post(
            "/api/predecir",
            json={**payload, "clima": {"temperatura_c": 8, "humedad_pct": 70, "lluvia_mm": 0}},
        )
        self.assertEqual(manual.status_code, 200, manual.text)
        self.assertEqual(manual.json()["fuente_clima"], "entrada")
        self.assertEqual(manual.json()["modo"], "escenario")
        band = self.client.post("/api/predecir", json={**payload, "franja": "06:00–10:59"})
        self.assertEqual(band.status_code, 200, band.text)
        self.assertLess(band.json()["prediccion"], data["prediccion"])

    def test_historical_mode_is_unchanged(self):
        data = self.client.post(
            "/api/predecir", json={"sucursal": "Hell's Kitchen", "fecha": "2023-06-15"}
        ).json()
        self.assertEqual(data["modo"], "historico")
        self.assertEqual(data["prediccion"], 572.92)

    def test_reports_and_persistence(self):
        response = self.client.post(
            "/api/predecir", json={"sucursal": "Astoria", "fecha": "2023-05-26", "periodo": 30}
        )
        data = response.json()
        self.assertEqual(len(data["tendencia"]), 1)
        report = self.client.post(
            "/api/reportes",
            json={
                "consulta_id": data["consulta_id"],
                "comentario": "Revisar unidades de la mañana.",
            },
        )
        self.assertEqual(report.status_code, 201)
        self.assertEqual(
            self.client.post(
                "/api/reportes", json={"consulta_id": 999999, "comentario": "Consulta desconocida."}
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                "/api/reportes", json={"consulta_id": data["consulta_id"], "comentario": "   "}
            ).status_code,
            422,
        )
        with TestClient(create_app(self.database)) as second:
            self.assertIn(
                data["consulta_id"], [row["id"] for row in second.get("/api/historial").json()]
            )

    def test_cors(self):
        headers = {"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"}
        response = self.client.options("/api/predecir", headers=headers)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")


if __name__ == "__main__":
    unittest.main()
    