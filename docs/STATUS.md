# Estado canónico — Míster 93/94

Fecha: 18-08-2026  
Versión: **1.0.0-h**  
Checkpoint: **1.0.0-h-release-hygiene-closed**

## Frentes cerrados

La línea A→G permanece cerrada funcionalmente, incluida la transición de temporada y los gates longitudinales 3/10/20/30. Antes del cierre técnico de H se completaron además H1 y H2 como prioridad de producto:

- economía jugable íntegramente en **pesetas (`ESP`, `ptas.`)**;
- separación de tesorería, presupuesto de fichajes, reserva operativa y presupuesto salarial;
- ingresos/gastos desglosados, deuda, amortización y financiación disciplinada;
- soak económico de 30 temporadas sin cajas negativas ni violaciones salariales activas;
- micro-pasada de assets obligatoria en cada pasada, auditable y no bloqueante.

## V1.0-H cerrada

H elimina la deuda de release que impedía hablar de candidato reproducible:

- `VERSION` es la única fuente de versión;
- API, frontend y manifiesto consumen o validan esa versión;
- documentación canónica separada del archivo histórico;
- build de producción reproducible con `npm ci && npm run build`;
- launcher único `python run_football9394.py` para frontend+API;
- saves, backups y logs fuera del repo;
- saves atómicos con `fsync`, validación, backup válido y recuperación de corrupción/truncado;
- diagnóstico de ejecución persistente en logs.

## Siguiente frente

**V1.0-I — UX cotidiana: Inicio, Continuar y procesos legibles.** El objetivo es que toda tarea multi-sistema muestre qué ocurrió, quién trabaja, estado, qué falta, consecuencias y si el usuario debe actuar.

## Histórico

Los documentos previos se conservan sin pérdida en `docs/archive/checkpoints/`. No son la fuente de verdad del estado actual.
