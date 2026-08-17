# Checkpoint 0.51 · NF9–NF12 · Carrera, proyecto, información y economía longitudinal

Fecha de cierre: 17/08/2026.

## Objetivo de la pasada

NF9–NF12 se implementan como una sola vertical, no como cuatro menús independientes. La carrera del entrenador, el consejo, la prensa y la economía consumen el mismo estado persistente y los mismos hechos del mundo. La regla de diseño es que una consecuencia importante pueda cruzar varios sistemas sin perder su origen: por ejemplo, una crisis financiera puede generar una exigencia de venta del consejo, convertirse en información/noticia y quedar resuelta por una venta real que también modifica la caja y el histórico económico.

## NF9 · Carrera profesional completa

Se añade estado profesional propio del mánager: reputación global y por países, candidaturas, entrevistas, ofertas, contrato activo, relaciones con clubes y memorias de carrera. El mercado de banquillos se construye con el estado real de las ligas, la presión del entrenador existente, la posición del club, su dimensión y el encaje con la reputación del usuario.

El usuario puede presentarse a una vacante, superar o fallar la entrevista, recibir una propuesta, aceptar un nuevo proyecto aun con contrato vigente y dimitir. Destitución y dimisión cierran contrato y etapa, pero no borran reputación, relaciones ni memoria. Las etapas anteriores modifican futuros reencuentros con un club.

El salto entre ligas no reinicia el universo. La liga que se abandona pasa al mundo de fondo con sus resultados ya disputados y la liga de destino se toma exactamente en el punto que ya llevaba simulado. Se reconstruyen sólo las superficies dependientes del club controlado.

La UI incorpora `Carrera`: contrato, objetivos, reputación por país, vacantes, candidaturas, ofertas, entrevistas, relaciones y etapas.

## NF10 · Consejo y proyecto

Cada club tiene un proyecto persistente con objetivo, posición esperada, filosofía, techo salarial, plantilla preferida, capacidad de staff, respaldo y decisiones. El proyecto conserva histórico entre temporadas y revisa objetivo/márgenes cuando cambia la campaña.

Las peticiones al consejo son decisiones condicionadas, no acciones gratuitas: presupuesto extra, ampliación de staff y prórroga ante una venta exigida dependen de respaldo y situación económica. Las ampliaciones aprobadas quedan bloqueadas para repetición dentro de la misma temporada; una misma presión de venta sólo puede recibir una prórroga.

La presión de venta nace exclusivamente de estrés financiero suficiente. Contiene ingreso requerido, restante, motivo y fecha límite. Una venta real reduce esa cantidad y puede resolverla, generando el correspondiente hecho/noticia causal.

## NF11 · Mundo informativo causal

Se materializa la cadena `hecho → rumor → noticia → reacción → consecuencia` mediante hilos persistentes. Consultas por jugadores, apertura de negociaciones, ofertas, fichajes, candidaturas, cambios de entrenador, resultados estructurales y decisiones del consejo pueden ser origen de información.

Un rumor no se fabrica al azar: siempre conserva el evento persistido que lo originó. Si pasan varios días sin confirmación, pierde certeza y se enfría sin convertirse en noticia verdadera. Si una operación avanza, consulta, negociación y fichaje se enlazan en el mismo hilo y la confirmación eleva la certeza al 100 %.

Noticias muestra ahora la cadena causal, certeza, reacciones y consecuencias, además del feed tradicional.

## NF12 · Economía longitudinal 2.0

La capa longitudinal no crea una segunda contabilidad. Clasifica los movimientos económicos que ya ejecuta la carrera: taquilla, socios, televisión, patrocinio, premios, salarios, primas, mercado, operaciones, servicio de deuda e inyecciones del consejo. Así se puede consultar el neto y el histórico por temporada sin volver a tocar la caja por registrar la explicación.

El motor registra ingresos de jornada, flujos mensuales, compras/ventas/cesiones y premios de final de temporada. Ascensos y descensos quedan como eventos estructurales del histórico económico. Si la tesorería no puede sostener la estructura, el club puede realizar una disposición de deuda real y esa crisis puede alimentar la presión de venta del consejo.

Economía expone salud financiera, desglose acumulado de la temporada, temporadas anteriores y presión de venta activa sin convertir el juego en un simulador contable.

## Superficies y API nuevas

- `GET /professional-career`
- `POST /jobs/{opportunity_id}/apply`
- `POST /job/resign`
- aceptación de ofertas compatible con ofertas profesionales y el flujo anterior de destitución
- `GET /board-project`
- `POST /board-project/requests/{request_type}`
- `GET /information-world`
- snapshot de economía ampliado con salud e histórico longitudinal

## Integridad y límites históricos

Los importes comerciales y contratos de entrenador que no disponen de fuente histórica individual se tratan como estimaciones de carrera, no como datos históricos documentados. La nueva capa económica reutiliza caja real del simulador y evita doble contabilización. Del mismo modo, el mundo informativo no inventa hechos para rellenar prensa: la incertidumbre se representa como incertidumbre y puede extinguirse.

## Validación de cierre

- NF9–NF12 dedicado: 10/10 PASS tras añadir el gate anti-exploit del consejo.
- Regresión backend seleccionada de cierre: se ejecutan en dos lotes para evitar el timeout de la suite pesada; el total certificado se registra en `project_football9394.json` y README.
- Frontend: gates SFC, calidad UI y sintaxis Vue ejecutados sobre las 26 SFC.
- `vite build`: no se declara PASS si el binario `vite` no está materializado en el entorno; los prechecks sí quedan diferenciados del build de producción.
