"""Coordina la predicción y su registro usando los contratos del dominio."""

from app.domain.contracts import Consulta, MotorPrediccion, RegistroConsultas


class DashboardService:
    def __init__(self, motor: MotorPrediccion, registro: RegistroConsultas):
        self.motor = motor
        self.registro = registro

    def consultar(self, consulta: Consulta) -> dict:
        resultado = self.motor.calcular(consulta)
        identificador = self.registro.guardar_consulta(consulta, resultado)
        return {**resultado, "consulta_id": identificador}
