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

**Profundización 0.49:** capacidad simultánea real según estructura de scouting, geografía compacta con tiempo de desplazamiento, calidad fijada al iniciar el encargo y obsolescencia efectiva de informes con pérdida de confianza/precisión. La UI expone ocupación, alcance y frescura.

**Comparación A/B/C 0.52:** `candidate_comparison` pone candidatos uno al lado del otro con lo que el club sabe de cada uno, no con la verdad del simulador. **No declara ganador cuando las horquillas se solapan**: decir cuál es mejor cuando el ojeo no da para tanto sería inventar precisión. Señala de quién se sabe más, a quién conviene observar y qué informe caducó. Una prueba fija que la salida coincide con `overall_range` del mercado, porque construida sobre la ficha cruda filtraba la media real —Dubovský salía con 74 cuando el club sólo podía estimar 71—.

Pendiente para cerrar NF1: **red de contactos**, y conocimiento territorial por competición, cuya primera pasada ya existe.

**Gate:** observar durante semanas produce una decisión mejor informada sin bloquear el fichaje de riesgo.

## NF2 — Planificación de plantilla y necesidades · P0

Convertir la lógica de necesidades que ya usa la IA en una herramienta del usuario: cobertura por puesto, contratos, exceso/escasez, edad, extranjeros, salario y prioridades.

Estados por jugador: mantener, renovar, vender, ceder, buscar sustituto, buscar competencia, desarrollar.

Bucle conectado:

`necesidad → encargo → candidatos → comparación → negociación → inscripción → efecto en plantilla`

**Primera vertical 0.48:** el mismo `squad_audit` de la IA alimenta ya un plan del usuario con cobertura por demarcación, déficit, nivel medio, contratos próximos, sucesión y posibles excedentes. Incluso una plantilla equilibrada devuelve una lectura de seguimiento en vez de un panel vacío.

**Profundización 0.49:** cada necesidad traduce su demarcación al filtro real de mercado y puede abrir la búsqueda directamente desde el planificador, reduciendo el salto entre diagnóstico y acción.

**Cierre 0.52:** decisiones persistentes por jugador y comparación A/B/C enlazada al plan, compartida con NF1: el panel del mercado enseña las tres alternativas y el veredicto dice si el club puede separarlas o todavía no.

## NF3 — Entrenamiento, preparación física y área médica · P0

Plan semanal compacto: recuperación, físico, defensa, ataque, táctica, balón parado y descanso; intensidad colectiva, foco individual, posición/rol, recuperación y preparación del siguiente rival.

Cadena real:

`entrenamiento → fatiga → riesgo de lesión → rendimiento → desarrollo → moral`

**Primera vertical 0.48 (área médica):** el parte de un jugador propio pasa por el responsable sanitario. La fecha canónica deja de presentarse automáticamente: se muestran intervalo de recuperación, confianza, recomendación y responsable según su competencia.

**Vertical jugable 0.49 (entrenamiento + carga):** plan semanal de siete días, intensidad colectiva y foco individual persistentes; cada sesión altera carga, fatiga, condición, riesgo y evidencia lenta de atributos. Los minutos de partido alimentan la misma carga y el parte médico consume ese mismo estado. Las lesiones de entrenamiento son eventos reales y una baja que invalida la convocatoria provoca reparación segura y explicación al usuario.

**Cierre funcional 0.50:** recuperación individual (`normal / reducida / recuperación / descanso`) y preparación específica del siguiente partido (`equilibrada / rival / ataque / defensa / balón parado`) comparten la misma carga y condición. El entrenamiento y los partidos hacen crecer familiaridad táctica según calidad del responsable; cambiar principios reduce temporalmente la asimilación. NF3 queda conectado de extremo a extremo con NF4 y NF8: preparar, entrenar, arriesgar y competir son ya un mismo estado persistente. Profundizaciones futuras podrán ampliar entrenamiento de nueva posición/rol, pero no bloquean el bucle funcional NF3.

**Gate:** el usuario entiende por qué un jugador está cargado, qué puede hacer y qué riesgo acepta.

### Gate conjunto P0

NF0 + NF1 + NF2 + NF3 forman el nuevo P0 funcional. Deben trabajar como un mismo proceso de club, no como cuatro pantallas aisladas.

## NF4 — Táctica 3.0: comportamiento, no sliders · P1

Separar comportamiento con balón y sin balón con lenguaje compatible con 1993. Añadir instrucciones individuales, balón parado, instrucciones sobre rival y familiaridad táctica.

Toda orden debe producir un cambio observable en el motor.

**Vertical funcional 0.50:** el plan persistente añade salida (`paciente / equilibrada / progresar pronto`), último tercio (`variar / centros / pase entre líneas`) y transición (`asegurar / equilibrada / contraatacar`) sobre la estructura táctica ya existente de mentalidad, ritmo, presión, línea, anchura, marcaje y fuera de juego. Se incorporan instrucciones individuales (función, libertad, presión), órdenes sobre amenazas rivales y lanzadores de córner/falta/penalti. La familiaridad tiene componentes de forma, posesión, presión y balón parado; cada orden llega al `TeamSheet` y modifica de forma trazable posesión, creación, selección de ocasión, presión, fatiga o balón parado. Los cambios de fase realizados durante el directo sincronizan el estado del motor para el siguiente tramo del partido.

**Gate NF4:** no existe un control táctico nuevo puramente descriptivo: fases, instrucciones individuales, rival, lanzadores y familiaridad tienen pruebas de llegada al motor y efecto observable.

## NF5 — Staff que informa · P1

Los empleados deben interpretar el mundo según su competencia: segundo entrenador, preparadores, médico, ojeador y secretario técnico. El usuario recibe opiniones de personas, no la verdad directa del motor.

**Vertical funcional 0.50:** se genera un paquete de informes persistentes/accionables desde el estado real de salud, plantilla, scouting, vestuario, táctica y negociaciones. Cada informe identifica autor, función, calidad, confianza, evidencia, urgencia y destino recomendado. La UI permite saltar desde el consejo a la superficie donde se resuelve el asunto. La información sensible mantiene la incertidumbre de NF0/NF1 en vez de revelar el valor oculto del simulador.

**Gate NF5:** cada informe debe poder responder quién lo firma, por qué lo cree, con qué confianza y qué acción concreta propone.

## NF6 — Gestión humana del vestuario · P1

Conectar jerarquía, grupos sociales, liderazgo, minutos, fichajes, ventas, disciplina, renovaciones, salida y memoria. Las conversaciones nacen de hechos; no se generan para llenar una bandeja.

**Vertical funcional 0.50:** el snapshot expone cohesión, grupos sociales y asuntos abiertos causados por hechos reales. Una renovación fallida puede abrir preocupación contractual; un fichaje puede preocupar al competidor directo por minutos/estatus; el usuario puede explicar, tranquilizar o ser firme, y también advertir/sancionar disciplinariamente. Las respuestas modifican satisfacción/relación y se archivan; nunca alteran la capacidad futbolística base. Los roles acordados al fichar se convierten en promesas que la selección real debe cumplir.

**Gate NF6:** no se crea una conversación sin causa persistida y toda respuesta deja una consecuencia humana trazable.

## NF7 — Contratos y mercado 2.0 · P1

Consultas, disponibilidad estimada, ofrecimientos, pruebas/cesiones cuando procedan, primas/cláusulas históricas, importancia de plantilla, ofertas simultáneas, agentes, ruptura de negociación y cadenas de sustitución.

Proceso único:

`scouting → interés → consulta → negociación club → negociación jugador → inscripción → anuncio → reacción`

**Vertical funcional 0.50:** antes de ofertar puede hacerse una consulta de disponibilidad con rango de precio/salario, postura del vendedor, confianza y responsable. La negociación temporal soporta rol de plantilla, prima, cláusula, competencia rival, contraoferta y retirada; la calidad del responsable influye de forma moderada en tiempos y exigencias. Una operación cerrada genera contrato, promesa de rol, noticia y reacción de vestuario. Se añaden **cesiones reales** dentro del mismo flujo: cuota, porcentaje de ficha, rol prometido, contrato temporal, persistencia, devolución automática el 30 de junio y restauración del club/contrato de origen sin penalizar una promesa que termina con el préstamo.

Pendiente de profundización posterior: ofrecer activamente jugadores a varios clubes y pruebas cuando el contexto histórico/competición lo permita. El núcleo negociación–contrato–reacción–cesión queda funcional.

**Gate NF7:** una operación debe sobrevivir guardado/carga y recorrer el ciclo completo sin teletransportes ni borrar sus consecuencias.

## NF8 — Partido: dirección y diagnóstico · P1

Prepartido con rival, tendencias, amenazas, bajas y plan del staff; directo con condición, rendimiento, ajustes, información del banquillo; postpartido causal: qué ocurrió, por qué y qué consecuencias deja.

No se persigue 3D. Se persigue densidad de decisión y comprensión.

**Vertical funcional 0.50:** la previa une rival, entrenador, calidad/confianza del informe, táctica conocida, amenazas, bajas, riesgos propios, familiaridad y foco de preparación. Durante el encuentro el banquillo expone consejo contextual, rendimiento de los once y fatiga; los cambios de fase táctica se aplican al estado vivo, no al siguiente partido. El cierre produce diagnóstico causal con razones y siguientes acciones apoyadas en lo sucedido realmente en el motor.

**Gate NF8:** el usuario puede recorrer `preparar → decidir → observar → corregir → entender` sin abandonar el contexto de partido y sin recibir diagnósticos desconectados de los hechos.

## NF9 — Carrera profesional completa · P2

Desempleo, búsqueda, candidatura, entrevista, contrato, proyecto, objetivos, reputación por países, relaciones con directivos, regreso, ofertas con contrato vigente, dimisión y memoria de etapas.

**Vertical funcional 0.51:** el mánager humano dispone de un mercado de banquillos persistente que cruza ligas y países, con encaje según reputación global/local, dimensión del club, presión y etapas anteriores. Puede presentarse a una vacante, pasar entrevista, recibir/aceptar una oferta aun teniendo contrato, dimitir y regresar a un club. Los contratos, reputación por país, relaciones con clubes y memorias profesionales viajan con la persona. Cambiar de liga intercambia control con la liga de fondo en el punto exacto ya simulado: ningún resultado se reinicia ni se recalcula.

**Gate NF9:** cambiar de empleo —incluido otro país— debe preservar mundo, historial, contrato, reputaciones, relaciones y etapas sin resetear resultados ni estado ajeno al club.

## NF10 — Consejo y construcción del proyecto · P2

Expectativas, presupuesto, salarios, tamaño de staff, peticiones, presión por vender, filosofía del club y respaldo al entrenador. Sólo decisiones que repercutan en fútbol.

**Vertical funcional 0.51:** cada club mantiene un proyecto con objetivo de temporada, filosofía, techo salarial, dimensión de plantilla/staff, respaldo y memoria de decisiones. Las peticiones de presupuesto, ampliación de estructura o prórroga ante una venta exigida dependen de respaldo y salud económica; no son botones gratuitos y una ampliación aprobada no puede explotarse repitiéndola en la misma temporada. Una crisis real puede generar presión de venta con cantidad y plazo; los ingresos de ventas reales reducen esa obligación. Al cambiar de temporada el proyecto conserva historia pero revisa objetivo y márgenes.

**Gate NF10:** toda petición debe tener condición, resolución, memoria y consecuencia futbolística/económica visible; el consejo no puede generar recursos infinitos por repetición.

## NF11 — Mundo informativo: prensa, rumores y reputaciones · P2

`hecho → rumor → noticia → reacción → consecuencia`

Los rumores deben nacer de operaciones, agentes, seguimiento, declaraciones y relaciones existentes; nunca de relleno aleatorio.

**Vertical funcional 0.51:** consultas de mercado, negociaciones, ofertas, fichajes, candidaturas, cambios de entrenador, competiciones, lesiones y decisiones del consejo alimentan hilos causales persistentes. Un rumor conserva su hecho origen, nivel de certeza y actores; si no aparece un hecho confirmatorio se enfría y muere, nunca se convierte solo en verdad por tiempo. Cuando llega la confirmación, el mismo hilo avanza a noticia, reacción y consecuencia en vez de generar historias paralelas inconexas.

**Gate NF11:** una noticia importante debe poder remontarse a un hecho persistido; un rumor no confirmado debe poder desaparecer sin crear hechos falsos.

## NF12 — Economía longitudinal 2.0 · P2

Taquilla, socios, televisión, premios, patrocinio, salarios, primas, fichajes, deuda y estructura para permitir crisis, ascensos transformadores, descensos y ventas necesarias sin convertir el juego en contabilidad.

**Vertical funcional 0.51:** la capa longitudinal reutiliza los movimientos de caja que ya ejecuta el motor y los clasifica por temporada —taquilla, socios, TV, patrocinio, premios, salarios, operaciones, deuda, primas y mercado— sin duplicar dinero. El cierre de temporada registra premios y los ascensos/descensos como cambios estructurales; el estado financiero produce una lectura de salud y, cuando la caja no aguanta, una reestructuración/deuda real puede desembocar en presión del consejo para vender. La interfaz resume causas y tendencia sin convertir la carrera en un libro mayor.

**Gate NF12:** la suma longitudinal explica la economía real del club sin doble contabilización y debe conservar temporadas, crisis y cambios de categoría tras guardar/cargar.

**Gate conjunto NF9–NF12 · 0.51:** carrera, consejo, información y economía deben compartir hechos y consecuencias. Un cambio de trabajo conserva el mundo; una crisis puede producir una exigencia del consejo y una noticia causal; una venta real altera simultáneamente caja, histórico económico y presión de proyecto.

## Orden de desarrollo aprobado

**NF0 Staff/responsabilidades → NF1 Scouting → NF2 Planificación de plantilla → NF3 Entrenamiento/médico → NF4 Táctica → NF5 Staff/informes → NF6 Vestuario → NF7 Mercado → NF8 Partido → NF9 Carrera → NF10 Consejo → NF11 Mundo/prensa → NF12 Economía.**

## Criterio final

El usuario debe dejar de manipular directamente variables ocultas del simulador y pasar a gestionar personas, información, decisiones y riesgos. El mundo puede ser profundo por debajo, pero la interfaz debe mantener siempre claro qué ocurre, quién trabaja, qué falta, qué opciones existen y qué consecuencias se esperan.

---

## Estado a 0.52 y huecos abiertos

**De las 73 rutas del backend, 72 tienen superficie de usuario.** La única que
faltaba era la comparación A/B/C, ya cableada. En cobertura de interfaz el plan
está prácticamente cerrado.

**Sin dueño, dentro del plan:**

- **NF1 · red de contactos.** No existe en el código.
- **NF7 · pruebas de jugadores** y ofrecer activamente a varios clubes.

**Fuera del plan, y conviene que entre:**

- **Hay futbolistas generados en el mundo.** La base original rellenó con su
  generador las plantillas de los clubes cuya liga no simulaba, y también hay
  relleno dentro de ligas modeladas. Se han eliminado 172 y quedan más. Un
  ojeador que informa sobre alguien que no existió choca de frente con NF1 y con
  el principio rector de distinguir dato histórico, inferido y generado. **Hace
  falta decidir qué se hace con ellos**: sustituirlos, marcarlos o excluirlos del
  ojeo.
- **El mundo ha crecido y el plan no lo recoge.** De 21 ligas a 41 competiciones
  y de 12.492 a 15.410 futbolistas. Afecta a NF1 —hay mucho más territorio que
  cubrir— y a NF9, cuyo mercado de banquillos cruza países que antes no existían.
- **Competiciones que faltan**: copas nacionales, sin las cuales la Recopa no
  tiene campeón al que clasificar, y fases de clasificación de selecciones.
- **Los clubes sin liga y los contenedores `Otros-` no generan estadísticas**, así
  que sus futbolistas están congelados. Diseño propuesto en
  `PLAN_CLUBES_EUROPEOS_93_94.md`.

