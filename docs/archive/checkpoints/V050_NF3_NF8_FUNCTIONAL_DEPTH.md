# Míster 93/94 · 0.50.0 — NF3 a NF8: profundidad funcional conectada

Fecha: 17/08/2026

Esta pasada no añade seis mini-juegos. Convierte NF3–NF8 en un único bucle de gestión: **preparar → entrenar → interpretar → gestionar personas → operar en mercado → competir → diagnosticar → volver a preparar**.

## NF3 · Entrenamiento, carga y medicina

- Recuperación individual: normal, reducida, recuperación o descanso.
- Preparación específica del próximo rival: equilibrada, rival, ataque, defensa o balón parado.
- Carga, fatiga, condición y riesgo médico siguen siendo el mismo estado compartido.
- El trabajo táctico y los partidos elevan familiaridad según la calidad del responsable.
- Los cambios de principios reducen temporalmente la familiaridad en vez de ser gratis.

## NF4 · Táctica 3.0

- Fases persistentes: salida, último tercio y transición.
- Se apoyan sobre mentalidad, ritmo, presión, línea defensiva, anchura, marcaje y fuera de juego ya existentes.
- Instrucciones individuales: función, libertad y presión.
- Instrucciones sobre rivales: marcaje estrecho, presión y orientación de pie.
- Lanzadores de córner, faltas y penaltis.
- Familiaridad de forma, posesión, presión y balón parado.
- Todo llega al motor; no son etiquetas de interfaz.
- Los cambios tácticos en vivo sincronizan inmediatamente el `live_match`.

## NF5 · Staff que interpreta

- Informes de salud, plantilla, scouting, vestuario, táctica y mercado.
- Autor, rol, competencia, confianza, evidencia, urgencia y acción recomendada.
- Acciones de informe enlazadas con Entrenamiento, Mercado, Plantilla o Táctica.
- El staff interpreta el estado disponible; no filtra automáticamente la verdad canónica.

## NF6 · Vestuario humano

- Cohesión y grupos sociales visibles.
- Preocupaciones causales por contrato, competencia tras fichajes y otros hechos persistidos.
- Respuestas: tranquilizar, explicar o ser firme.
- Disciplina: advertencia y multa semanal según contexto.
- Las consecuencias afectan satisfacción/relaciones, nunca la habilidad base del jugador.
- El rol prometido al fichar se convierte en compromiso que se evalúa mediante alineaciones reales.

## NF7 · Mercado y contratos 2.0

- Consulta de disponibilidad antes de ofertar.
- Rangos, postura del vendedor, confianza y responsable de la consulta.
- Negociación temporal con rol, prima, cláusula, rival, contraoferta y retirada.
- Firma → contrato → promesa → noticia → reacción de vestuario.
- Cesiones completas: cuota, porcentaje de ficha, rol, contrato temporal y devolución automática el 30 de junio.
- Al terminar una cesión se restauran club y contrato anteriores y se cierra la promesa de rol sin castigo artificial.

## NF8 · Dirección y diagnóstico de partido

- Briefing previo con rival, entrenador, confianza, tendencias conocidas, amenazas, bajas, riesgo propio, familiaridad y preparación.
- Rendimiento individual y fatiga durante el directo.
- Consejo contextual del banquillo.
- Ajustes de fase durante el partido aplicados al siguiente tramo del motor.
- Diagnóstico postpartido con causas y acciones siguientes derivadas del encuentro.

## Integración y bugs corregidos

- Lesiones de entrenamiento siguen reparando convocatoria de forma segura.
- La preparación del rival, familiaridad y táctica usan un único estado persistente.
- Los informes del staff abren la acción pertinente en vez de quedar como texto muerto.
- La promesa contractual de rol y la reacción del vestuario sobreviven al cierre de la operación.
- Las cesiones no convierten al jugador en un traspaso permanente ni pierden su contrato de origen.

## Validación 0.50

- `test_football9394_nf3_nf8_functional.py`: **11/11 PASS**.
- Regresión NF0/NF1/NF2/NF3 previa + mercado + motor + contexto de jornada + vestuario + F1–F8: **44/44 PASS**.
- Web/API: **16/16 PASS**.
- Total seleccionado ejecutado para el cierre 0.50: **71/71 PASS**.
- Frontend: **SFC PASS · UI PASS · Vue 25/25 PASS**.
- `vite build`: no certificado en este entorno porque el binario/dependencias de Vite no están materializados.
- El gate histórico pesado de `test_football9394_manager_career.py` no se vuelve a declarar PASS: en esta sesión supera la ventana de ejecución después de cinco casos sin fallo. Los grupos directamente afectados por NF3–NF8 sí están recertificados arriba.

## Lo que no se declara cerrado artificialmente

NF3–NF8 tienen ya una vertical jugable conectada. Queda profundidad futura legítima —por ejemplo entrenar una nueva posición/rol, ofrecer jugadores masivamente a clubes o ampliar pruebas/observación—, pero ya no son cascarones: cada NF modifica decisiones, estado persistente o comportamiento del motor y comparte consecuencias con los demás.
