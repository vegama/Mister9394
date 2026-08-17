# Míster 93/94 — Plan de profundidad funcional inspirado en Football Manager

Estado inicial: **checkpoint 0.46.0**  
Fecha de apertura: **17/08/2026**  
Objetivo: elevar la gestión del club hasta una profundidad comparable en filosofía a Football Manager sin copiar su interfaz, sin introducir burocracia innecesaria y sin romper la identidad histórica 1993-94.

> Nota de nomenclatura: el repositorio ya contiene un plan histórico `F1–F8` cerrado. Para no colisionar con él, las fases F0–F12 definidas en esta nueva etapa se versionan internamente como **NF0–NF12** (Nueva Funcionalidad), manteniendo exactamente el orden y significado aprobados.

## Principio rector

La profundidad no debe salir de añadir menús, sino de conseguir que el usuario gestione un club compuesto por personas, información imperfecta, responsabilidades, decisiones y consecuencias conectadas.

Cada sistema nuevo debe responder siempre a seis preguntas:

1. **Qué sé.**
2. **Quién me lo dice.**
3. **Con qué fiabilidad.**
4. **Qué puedo hacer.**
5. **Qué consecuencias puede tener.**
6. **Cuándo volveré a saber algo.**

Reglas UX permanentes:

- profundidad sin burocracia;
- las decisiones importantes deben ser naturales de localizar y resolver;
- delegar no elimina profundidad: cambia quién trabaja y cómo llega la información;
- el dato histórico, el dato inferido y el dato generado por la carrera se distinguen siempre;
- ningún control será decorativo: toda instrucción debe afectar a un sistema real;
- la ambientación y los procesos deben sentirse propios de 1993-94, no de una plataforma moderna de datos.

## NF0 — Arquitectura humana del club · P0 · ACTIVO

Crear estructura persistente de empleados y responsabilidades reales.

Roles base:

- segundo entrenador;
- entrenadores de primer equipo;
- entrenador de porteros cuando el tamaño del club lo justifique;
- fisioterapeuta / responsable médico;
- ojeadores;
- jefe de ojeadores cuando la estructura lo justifique;
- secretario técnico / director deportivo cuando exista en fuente o la dimensión del club lo justifique.

Atributos funcionales, no decorativos: entrenamiento, táctica, disciplina, juicio de capacidad/potencial, conocimiento de mercado, negociación, fisioterapia y trabajo con jóvenes.

Matriz persistente:

`responsabilidad → responsable → competencia → carga → estado → resultado`

El usuario puede asumir personalmente una responsabilidad o delegarla en personal elegible. La misma carrera debe poder jugarse con un mánager controlador o con mucha delegación.

**Primera pasada 0.47:** infraestructura persistente por club, staff generado claramente etiquetado cuando no exista fuente, atributos, responsabilidades, reasignación desde UI/API, carga y calidad estimada.

**Segunda pasada 0.48:** la delegación deja de ser sólo organizativa. Cada responsabilidad expone una eficacia operativa común (`competencia + carga + control directo`) que ya consumen scouting, informes del rival, área médica y negociación de fichajes. El responsable, su calidad y la confianza quedan visibles para el usuario.

**Gate NF0:** una responsabilidad cambiada de responsable debe persistir en guardado/carga, validar que el empleado sea elegible y mantener estructuras distintas al cambiar de club.

## NF1 — Scouting y conocimiento imperfecto · P0

Un jugador externo no debe revelar automáticamente toda su verdad. Estados de conocimiento: desconocido → referencia superficial → observado → informe fiable → conocimiento profundo.

La habilidad real no cambia; cambia la precisión del conocimiento. Deben existir rangos, fecha del informe, confianza, calidad del ojeador, partidos observados, conocimiento por país/liga/club y obsolescencia.

Ambientación 1993: contactos, prensa, informes, desplazamientos y material disponible; no una base de datos omnisciente.

**Primera vertical 0.48:** conocimiento persistente por jugador, mercado con estimaciones/rangos en lugar de verdad canónica, encargo de informe con días reales, responsable y calidad, informes fiables y profundización posterior, memoria del informe y watchlist automática.

**Profundización 0.49:** capacidad simultánea real según estructura de scouting, geografía compacta con tiempo de desplazamiento, calidad fijada al iniciar el encargo y obsolescencia efectiva de informes con pérdida de confianza/precisión. La UI expone ocupación, alcance y frescura. Pendiente para cerrar NF1: conocimiento territorial/por competición más fino, red de contactos y comparación A/B/C integrada.

**Gate:** observar durante semanas produce una decisión mejor informada sin bloquear el fichaje de riesgo.

## NF2 — Planificación de plantilla y necesidades · P0

Convertir la lógica de necesidades que ya usa la IA en una herramienta del usuario: cobertura por puesto, contratos, exceso/escasez, edad, extranjeros, salario y prioridades.

Estados por jugador: mantener, renovar, vender, ceder, buscar sustituto, buscar competencia, desarrollar.

Bucle conectado:

`necesidad → encargo → candidatos → comparación → negociación → inscripción → efecto en plantilla`

**Primera vertical 0.48:** el mismo `squad_audit` de la IA alimenta ya un plan del usuario con cobertura por demarcación, déficit, nivel medio, contratos próximos, sucesión y posibles excedentes. Incluso una plantilla equilibrada devuelve una lectura de seguimiento en vez de un panel vacío.

**Profundización 0.49:** cada necesidad traduce su demarcación al filtro real de mercado y puede abrir la búsqueda directamente desde el planificador, reduciendo el salto entre diagnóstico y acción. Pendiente: decisiones persistentes por jugador y comparación A/B/C enlazada al plan.

## NF3 — Entrenamiento, preparación física y área médica · P0

Plan semanal compacto: recuperación, físico, defensa, ataque, táctica, balón parado y descanso; intensidad colectiva, foco individual, posición/rol, recuperación y preparación del siguiente rival.

Cadena real:

`entrenamiento → fatiga → riesgo de lesión → rendimiento → desarrollo → moral`

**Primera vertical 0.48 (área médica):** el parte de un jugador propio pasa por el responsable sanitario. La fecha canónica deja de presentarse automáticamente: se muestran intervalo de recuperación, confianza, recomendación y responsable según su competencia.

**Vertical jugable 0.49 (entrenamiento + carga):** plan semanal de siete días, intensidad colectiva y foco individual persistentes; cada sesión altera carga, fatiga, condición, riesgo y evidencia lenta de atributos. Los minutos de partido alimentan la misma carga y el parte médico consume ese mismo estado. Las lesiones de entrenamiento son eventos reales y una baja que invalida la convocatoria provoca reparación segura y explicación al usuario. Pendiente: familiaridad táctica, preparación rival más profunda y recuperación individual específica.

**Gate:** el usuario entiende por qué un jugador está cargado, qué puede hacer y qué riesgo acepta.

### Gate conjunto P0

NF0 + NF1 + NF2 + NF3 forman el nuevo P0 funcional. Deben trabajar como un mismo proceso de club, no como cuatro pantallas aisladas.

## NF4 — Táctica 3.0: comportamiento, no sliders · P1

Separar comportamiento con balón y sin balón con lenguaje compatible con 1993. Añadir instrucciones individuales, balón parado, instrucciones sobre rival y familiaridad táctica.

Toda orden debe producir un cambio observable en el motor.

## NF5 — Staff que informa · P1

Los empleados deben interpretar el mundo según su competencia: segundo entrenador, preparadores, médico, ojeador y secretario técnico. El usuario recibe opiniones de personas, no la verdad directa del motor.

## NF6 — Gestión humana del vestuario · P1

Conectar jerarquía, grupos sociales, liderazgo, minutos, fichajes, ventas, disciplina, renovaciones, salida y memoria. Las conversaciones nacen de hechos; no se generan para llenar una bandeja.

## NF7 — Contratos y mercado 2.0 · P1

Consultas, disponibilidad estimada, ofrecimientos, pruebas/cesiones cuando procedan, primas/cláusulas históricas, importancia de plantilla, ofertas simultáneas, agentes, ruptura de negociación y cadenas de sustitución.

Proceso único:

`scouting → interés → consulta → negociación club → negociación jugador → inscripción → anuncio → reacción`

## NF8 — Partido: dirección y diagnóstico · P1

Prepartido con rival, tendencias, amenazas, bajas y plan del staff; directo con condición, rendimiento, ajustes, información del banquillo; postpartido causal: qué ocurrió, por qué y qué consecuencias deja.

No se persigue 3D. Se persigue densidad de decisión y comprensión.

## NF9 — Carrera profesional completa · P2

Desempleo, búsqueda, candidatura, entrevista, contrato, proyecto, objetivos, reputación por países, relaciones con directivos, regreso, ofertas con contrato vigente, dimisión y memoria de etapas.

## NF10 — Consejo y construcción del proyecto · P2

Expectativas, presupuesto, salarios, tamaño de staff, peticiones, presión por vender, filosofía del club y respaldo al entrenador. Sólo decisiones que repercutan en fútbol.

## NF11 — Mundo informativo: prensa, rumores y reputaciones · P2

`hecho → rumor → noticia → reacción → consecuencia`

Los rumores deben nacer de operaciones, agentes, seguimiento, declaraciones y relaciones existentes; nunca de relleno aleatorio.

## NF12 — Economía longitudinal 2.0 · P2

Taquilla, socios, televisión, premios, patrocinio, salarios, primas, fichajes, deuda y estructura para permitir crisis, ascensos transformadores, descensos y ventas necesarias sin convertir el juego en contabilidad.

## Orden de desarrollo aprobado

**NF0 Staff/responsabilidades → NF1 Scouting → NF2 Planificación de plantilla → NF3 Entrenamiento/médico → NF4 Táctica → NF5 Staff/informes → NF6 Vestuario → NF7 Mercado → NF8 Partido → NF9 Carrera → NF10 Consejo → NF11 Mundo/prensa → NF12 Economía.**

## Criterio final

El usuario debe dejar de manipular directamente variables ocultas del simulador y pasar a gestionar personas, información, decisiones y riesgos. El mundo puede ser profundo por debajo, pero la interfaz debe mantener siempre claro qué ocurre, quién trabaja, qué falta, qué opciones existen y qué consecuencias se esperan.
