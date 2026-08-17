# V1 · Plan ambicioso de carrera

## Objetivo

Míster 93/94 debe ser profundo, divertido, bello, fácil de leer y capaz de producir carreras memorables durante muchas temporadas sin convertir la gestión en burocracia. El bucle sigue siendo **Continuar → ocurre algo relevante → decidir → jugar → ver consecuencias**.

## Regla de universo preferida · reparto eterno

La política predeterminada es `frozen_attributes_dynamic`.

- La edad visible y lógica de cada futbolista queda anclada a su edad de 1993-94.
- No hay decadencia automática por edad, retirada por edad, cantera promovida ni newgens.
- El reparto histórico inicial permanece disponible indefinidamente salvo decisiones del propio mundo no ligadas a edad.
- Los atributos **sí evolucionan**: rendimiento, minutos, entrenador, compatibilidad, lesiones, forma, experiencia y tutela producen mejoras o deterioros lentos y específicos.
- Un futbolista puede cambiar de rol, aprender, perder recursos físicos tras lesiones o ganar lectura/regularidad sin «cumplir años».
- El modo cronológico tradicional continúa disponible de forma explícita para quien lo quiera, pero no gobierna la experiencia por defecto.

Esta es una concesión consciente al realismo histórico. El realismo prioritario pasa a ser el de las decisiones, las relaciones y el fútbol; no la desaparición del reparto original.

## P1 · Carrera profesional del mánager

Reputación multidimensional, ofertas mientras trabajas, dimisión, candidaturas, entrevistas, contratos y proyectos de club. Movilidad entre ligas y países debe conservar el mundo existente, nunca reconstruir resultados.

## P2 · Conocimiento imperfecto y scouting 1993

Conocimiento por jugador/país/competición, estimaciones con incertidumbre y observación progresiva. El scouting reduce ignorancia; nunca modifica la capacidad real del futbolista.

## P3 · Percepción subjetiva del entrenador

Cada entrenador interpreta al futbolista desde su sistema y preferencias. Esa percepción gobierna XI, rotación, fichajes, renovaciones, descartes, cesiones y desarrollo compatible. La valoración neutral permanece separada.

## P4 · Vestuario, liderazgo y memoria

Capitán, líderes, competencia por puestos, tutelas entre el reparto inicial, promesas de rol, reacción a ventas/lesiones importantes y relaciones que sobreviven a cambios de club. Nada de diálogo por obligación: los hechos futbolísticos construyen la relación.

## P5 · Táctica e IA 2.0

Preparación específica del rival, contramedidas, ajustes durante partido y técnicos que expresan identidades reconocibles. El postpartido debe explicar causas sin revelar modificadores secretos.

## P6 · Partido 2.0 y firma individual

Calibrar no sólo goles sino creación, tiros, balón parado, tarjetas, penaltis, lesiones y contribución por perfil. Los atributos y roles deben dejar firmas estadísticas observables.

## P7 · Mercado como ecosistema

Planificación a meses vista, sustituciones encadenadas, competencia por objetivos, agentes, preferencias del jugador y movimientos explicables por necesidad, dinero, entrenador y oportunidad.

## P8 · Reglamento 1993-94 permanente

El marco reglamentario queda congelado deliberadamente en 1993-94 durante toda la historia alternativa. No se introduce Bosman, no se liberalizan posteriormente los cupos de extranjeros y no aparecen ventanas o reformas modernas sólo porque avance el calendario. Las reglas históricas de inicio son parte del desafío permanente de la partida. Los resultados, carreras, fichajes y cambios de poder sí evolucionan libremente dentro de ese marco.

## P9 · Selecciones y mundo conectado

Carrera internacional del mánager, convocatorias, torneos y reputación internacional. Los mismos jugadores del reparto eterno pueden construir largas historias de selección; no es necesario sustituir generaciones para producir profundidad.

## P10 · Gate de una partida memorable

Playtests con clubes grandes, medios, modestos y carreras nómadas; gates de 3, 10, 20 y 30 temporadas. Medir realismo de decisiones, diversión, belleza, claridad, profundidad, coherencia económica/deportiva y capacidad de recordar historias concretas.

## Estado actual

**P1–P10 cerrados en 0.20.0.** El plan ambicioso de carrera queda implementado sobre el reparto eterno y el marco reglamentario 1993-94 permanente.

- P6 persiste un boxscore causal por futbolista y una firma observable por perfil/rol; el gate de 120 partidos valida entorno y diferenciación estadística.
- P7 mantiene planes de plantilla a seis meses, riesgo contractual, competencia por objetivos, preferencias del jugador, presión del agente y compras de sustitución encadenadas después de ventas.
- P8 repara saves manipulados hacia `frozen_1993_94` y audita sustituciones, puntos, ventanas y extranjeros en años futuros sin Bosman ni liberalización automática.
- P9 permite compatibilizar club y selección, aceptar/dejar cargos, mantener convocatoria de 22, jugar amistosos y un Mundial de 24 equipos cada cuatro años, y archiva internacionalidades y contribuciones individuales.
- P10 ejecuta cuatro carreras reales de diez partidos y una carrera nómada; además comprueba a 3/10/20/30 temporadas los invariantes de edad congelada, cero newgens y reglamento permanente. Esos probes longitudinales no se presentan como resultados deportivos simulados: certifican invariantes sin fabricar temporadas.

La auditoría reproducible queda en `backend/tools/audit_football9394_plan_closed.py` y su última salida en `docs/p6_p10_closure_audit.json`. El detalle del cierre está en `docs/V020_P6_P10_PLAN_CLOSED.md`.
