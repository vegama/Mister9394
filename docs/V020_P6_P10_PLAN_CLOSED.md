# 0.20 · P6–P10 cerrados · plan ambicioso completo

## Resultado

El checkpoint 0.20 cierra **P6, P7, P8, P9 y P10** y, con ellos, el plan P1–P10 de `V1_AMBITIOUS_CAREER_PLAN.md`. El criterio de cierre no es “hay una función con ese nombre”: cada bloque queda conectado al runtime persistente, expuesto cuando corresponde en API/UI y protegido por gates dirigidos.

## P6 · Partido 2.0 y firma individual

El motor persiste un boxscore causal por futbolista a partir de acciones que realmente resuelve: goles, asistencias, tiros, tiros a puerta, ocasiones creadas, balón parado, penaltis, paradas, faltas, tarjetas, fueras de juego, lesiones y segundas jugadas. No se inventan pases o entradas que el motor no simula toque a toque.

Cada jugador recibe además una firma observable dependiente de rol y atributos (`portero`, `recuperador`, `creador`, `desborde`, `aereo`, `balon_parado`, `finalizador`). La ficha de jugador y el postpartido pueden enseñar esa huella sin sustituir la valoración neutral por una “verdad” oculta.

El audit reproducible de 120 partidos obtiene 2,642 goles, 21,700 tiros, 9,308 tiros a puerta, 4,550 córners y 12,767 faltas por encuentro. Los checks de firma confirman, entre otras diferencias, que porteros acumulan paradas, creadores producen más ocasiones, especialistas concentran balón parado y finalizadores rematan con mayor frecuencia.

## P7 · Mercado como ecosistema

Los clubes mantienen un plan de reclutamiento a seis meses con necesidades posicionales, urgencia, riesgo contractual, caja y encaje con el entrenador. El mercado mensual se divide en pulsos: una primera venta puede alterar la plantilla y provocar una compra de sustitución en la segunda oleada, dejando una `replacement_chain` persistente.

La negociación del usuario incorpora preferencias del futbolista —salario, rol, salto deportivo, encaje y deseo de salir—, presión del agente derivada de contrato/satisfacción/competencia y rivales concretos capaces de ganar realmente la operación. Las razones se guardan y pueden explicarse; no son loterías por ID.

## P8 · Reglamento 1993-94 permanente

`era_policy.py` convierte la regla de producto en contrato auditable. Al cargar incluso un save manipulado, el runtime reimpone `frozen_1993_94`. El informe de integridad comprueba sustituciones, puntos por victoria, semántica de ventanas y restricciones de extranjeros en años futuros. El avance de calendario no activa Bosman, liberalizaciones ni reformas modernas.

## P9 · Selecciones y mundo conectado

El mánager puede aceptar un cargo de selección sin abandonar el club, dimitir de él, mantener una convocatoria de 22 y regenerarla automáticamente. Los días internacionales usan esa selección persistente. La reputación internacional cambia con resultados y rondas.

Cada cuatro años desde 1994 se puede disputar un campeonato mundial de **24 selecciones** con estructura congelada de seis grupos, clasificación de mejores terceros y eliminatorias. Los participantes proceden de países identificables en la fuente; los resultados son historia alternativa y se marcan explícitamente como no históricos.

Las internacionalidades ya dejan historia individual: titularidades, caps, goles, asistencias, partidos/goles de torneo y un historial compacto por futbolista. La ficha del jugador expone el resumen internacional.

## P10 · Gate de una partida memorable

El gate técnico ejecuta carreras reales de diez partidos con cuatro perfiles: favorito, medio, modesto de Primera y categoría inferior. También fuerza una carrera nómada con dos cambios de club y comprueba que etapas, mundo y memoria sobreviven.

Para 3/10/20/30 temporadas se ejecutan probes de invariantes: edad congelada, cero jugadores generados y reglamento `frozen_1993_94`. Esos probes **no se etiquetan como temporadas deportivas simuladas**; su misión es impedir deriva de reglas/edad sin fabricar campeones o clasificaciones que no se han calculado.

Diversión percibida, belleza y ganas de continuar siguen siendo juicios humanos y el gate lo declara con `human_score_fabricated=false`. El plan se cierra técnicamente sin convertir una cifra automática en una opinión humana falsa.

## Evidencia de cierre

- `backend/tests/test_football9394_p6_p10_plan_closed.py`: 8/8 PASS.
- Regresión focal P4–P9, motor, mercado, economía, carrera, movilidad, torneos y API: 72/72 PASS en grupos aislados.
- `backend/tools/audit_football9394_plan_closed.py`: PASS para P6 y P10; salida `docs/p6_p10_closure_audit.json`.
- Frontend: `check:sfc`, `check:ui` y `check:vue` PASS; 23/23 SFC con sintaxis válida.
- `npm run build`: no certificado en este entorno porque falta el binario `vite` al no estar materializadas las dependencias Node. Los tres gates previos sí pasan.
- Los antiguos tests completos de rollover/longitudinal son demasiado lentos para la ventana de esta ejecución y no se marcan fraudulentamente como recertificados. Los gates P10 separan explícitamente jugabilidad real e invariantes de horizonte largo.

## Estado siguiente

No queda un P11 implícito. **El plan P1–P10 está cerrado.** Cualquier trabajo posterior debe abrir un nuevo plan de producto a partir de playtest, no arrastrar como “pendiente” una casilla de este roadmap.
