AGENTS.md - Ejemplo Completo: Proyecto "MedLogger"

Este documento define la Constitución del Agente para el proyecto MedLogger, una plataforma de logging médico. Todas las reglas aquí definidas son ejecutables y se hacen cumplir automáticamente a través del linter de Trifecta.




1. Visión y Principios

El proyecto MedLogger se construye sobre los siguientes principios:

•
Seguridad en Primer Lugar: Todos los datos de pacientes están protegidos por defecto.

•
Arquitectura Limpia: La lógica de negocio está completamente separada de la infraestructura.

•
Funciones Puras: La mayoría del código son funciones puras para facilitar el testing y la verificación.

•
Documentación Viva: El código es autodocumentado a través de tipos y comentarios.




2. Límites Arquitectónicos (Architectural Boundaries)

La arquitectura de MedLogger sigue el patrón de Arquitectura Limpia. Hay cuatro capas principales:

1.
core/: Lógica de negocio pura (sin dependencias externas)

2.
domain/: Entidades y casos de uso (depende de core/)

3.
infrastructure/: Acceso a datos, APIs externas (depende de domain/)

4.
api/: Controladores HTTP y puntos de entrada (depende de infrastructure/)

La regla fundamental es: cada capa solo puede importar de capas inferiores (más cercanas a core/).

YAML
