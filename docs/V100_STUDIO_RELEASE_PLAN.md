# Míster 93/94 — Plan de trabajo de estudio para v1.0.0

## Decisión de dirección

La v1.0.0 no será una carrera por añadir más pantallas ni por alcanzar un 100 % artificial de assets. La base actual ya tiene suficiente amplitud funcional para entrar en fase de producto.

La prioridad de cierre es:

1. **que jugar sea claro y cómodo**;
2. **que las decisiones futbolísticas sean interesantes y tengan consecuencias comprensibles**;
3. **que partido, temporada y carrera sean fiables de principio a fin**;
4. **que todas las pantallas compartan una misma gramática visual y de interacción**;
5. **que la simulación y la IA no produzcan situaciones absurdas**;
6. **que guardar, cargar, avanzar y cambiar de temporada no rompan el mundo**;
7. **que la presentación histórica sea sólida**;
8. **seguir completando assets en paralelo, sin bloquear los frentes anteriores ni inventar recursos históricos**.

El principio de producto para v1 es sencillo: **un usuario que no haya visto nunca el juego debe poder empezar una carrera, entender qué necesita hacer, preparar un equipo, jugar o simular un partido, interpretar sus consecuencias y llegar a la siguiente temporada sin ayuda externa**.

---

## Qué aporta cada perspectiva de la revisión

### Diseño de producto

- Reducir ruido visual y paneles que compiten entre sí.
- Mantener densidad de manager, pero con jerarquía: identidad → situación → decisión → detalle.
- Una acción primaria evidente por contexto.
- Usar color para estado y prioridad, no como decoración.
- Fotos, escudos y estadios deben reforzar orientación e inmersión, nunca sostener la usabilidad por sí solos.

### Experiencia de jugador

- El usuario debe saber siempre **dónde está, qué ha cambiado, qué requiere atención y qué pasa si no actúa**.
- Navegar a una ficha, noticia, rival o competición no debe hacer perder el contexto anterior.
- Continuar debe ser el corazón del juego y detenerse ante decisiones realmente relevantes, no por burocracia.
- Los estados vacíos y errores deben explicar la siguiente acción posible.
- Las acciones frecuentes deben requerir pocos clics y no obligar a recordar dónde estaba cada función.

### Jugadores de managers

- Más fútbol y consecuencias; menos administración por obligación.
- El once, táctica, forma, disponibilidad, rival, mercado y resultados deben ser legibles en segundos.
- El juego tiene que permitir delegar o resolver rápido lo rutinario, pero ofrecer profundidad al que quiera entrar.
- El mundo debe explicar por qué ocurren fichajes, cambios, decisiones de entrenadores y conflictos sin revelar fórmulas internas.
- Una temporada tiene que dejar recuerdos: partidos, campeones, jugadores, decisiones y cambios de carrera.

### Beta / QA

- Los bugs más peligrosos para v1 son los de continuidad: doble acción, recarga, atrás/adelante, partido a medio terminar, transición de temporada, datos que se actualizan a medias, saves viejos y combinaciones raras de navegación.
- Los tests largos son necesarios para release, pero no pueden ser la única protección diaria.
- Cada frente debe tener smoke tests rápidos y una certificación destructiva posterior.

### Dirección de estudio

- **Feature freeze de grandes sistemas para v1.0.0.** Sólo entra una nueva mecánica si repara una carencia clara del bucle principal.
- No perseguir 100 % de assets a costa de jugabilidad.
- No marcar un frente como cerrado por “tener pantalla”; debe superar su gate de experiencia y regresión.
- La versión se etiqueta v1.0.0 sólo después de dos candidatos de release consecutivos sin bloqueadores P0/P1.

---

# Estado de ejecución tras Ola 4

- **A — contrato de lanzamiento:** activo y con gates separados smoke/release.
- **B+C+D — Inicio + Plantilla/XI/Táctica + jornada de partido:** **candidato de cierre funcional** tras cuatro olas; mantener bajo regresión, no seguir expandiendo features.
- Ola 4 certifica segunda amarilla→roja, lesión con cambios agotados, táctica de descanso, calendario aplazado/sin rival/vacío y una única verdad de lesión/sanción entre Inicio → Plantilla → ficha → Táctica/previa → noticia → calendario.
- Certificación backend dirigida acumulada de la última pasada: **19/19**; frontend estático: **28/28 SFC + structure + UI quality**.
- El build Vite completo sigue pendiente de un entorno con dependencias instaladas; no se considera verde mientras `vite` no esté disponible.
- **Assets:** siguen congelados como frente secundario; Ola 4 = 0 trabajo de recursos.
- **E — Mercado, staff, entrenamiento y decisiones delegables:** **activo (Ola 1)**. Ya existe continuidad necesidad → seguimiento → informe → consulta → negociación, ownership/delegación explícitos, borrador/guardado de entrenamiento y recuperación de contexto de Mercado tras F5. Siguiente paso: Ola 2 destructiva sobre cambios de responsable, contraofertas, renovaciones, mercado cerrado, carga del staff y alternativas A/B/C.

---

# Plan de ejecución

## V1.0-A — Baseline y contrato de lanzamiento

**Objetivo:** congelar qué significa “v1.0.0” y evitar expansión infinita.

Trabajo:

- Inventario de las rutas y acciones disponibles en los 22 espacios funcionales actuales.
- Clasificar problemas como P0 bloqueador, P1 importante, P2 pulido, P3 futuro.
- Crear matriz de recorrido crítico y responsable técnico por subsistema.
- Separar tests en dos grupos:
  - **smoke diario**: frontend estático, API, partida, partido, guardado/carga y transición básica;
  - **release gate**: varias temporadas, formatos, mercado, carrera, IA y casos destructivos.
- Mantener compatibilidad de saves del checkpoint siempre que sea razonable; cuando haga falta migración, debe ser explícita y probada.

**Gate A:** existe una lista finita de bloqueadores de v1, cada uno con prueba o criterio verificable.

---

## V1.0-B — Primeros 15 minutos y orientación permanente

Pantallas principales: `CareerSetup`, `HomeDashboard`, `ManagerSidebar`, `ManagerTopbar`.

**Objetivo:** alguien nuevo puede empezar y comprender el juego sin manual.

Trabajo:

- Revisión completa de Nueva carrera: equipo, modo de universo y consecuencias de cada elección.
- El Inicio debe ser un despacho, no un dashboard genérico:
  - próximo partido;
  - asuntos que necesitan decisión;
  - estado deportivo;
  - confianza/objetivo del club;
  - noticias o cambios relevantes;
  - CTA Continuar siempre localizable.
- Agrupar decisiones por urgencia y evitar que cinco avisos del mismo sistema parezcan cinco problemas distintos.
- Cada aviso debe abrir exactamente la pantalla/objeto donde se resuelve.
- Añadir retorno contextual después de resolver una incidencia.
- Revisar nombres, microcopy y estados para eliminar términos técnicos internos.
- Atajos de teclado sólo como ayuda; ninguna acción debe depender de ellos.

**Gate B:** playtest “usuario nuevo”: crear carrera → localizar siguiente acción → resolver una incidencia → preparar el primer partido sin instrucciones externas.

---

## V1.0-C — Plantilla, jugador, disponibilidad, once y táctica

Pantallas principales: `SquadWorkspace`, ficha de jugador, `LineupPitch`, `TacticsWorkspace`, `TrainingWorkspace`.

**Objetivo:** convertir la preparación del equipo en el mejor flujo cotidiano del juego.

Trabajo:

- Ficha de jugador canónica: identidad, posición/rol, nivel, forma, moral, contrato y disponibilidad visibles antes del detalle.
- Mantener la foto visible sin sacrificar información útil.
- Unificar disponibilidad física: lesión, sanción, fatiga/carga y riesgo deben leerse desde Plantilla y desde selección de XI.
- XI:
  - campo como interacción principal;
  - compatibilidad posicional visible;
  - banquillo con forma/condición/estado;
  - sustitución campo↔banquillo directa;
  - explicación local de por qué el once no es legal;
  - “mejor once disponible” como atajo, no como requisito.
- Táctica:
  - mostrar primero intención del plan;
  - después instrucciones y roles;
  - advertir incompatibilidades reales, no llenar la pantalla de warnings.
- Entrenamiento:
  - separar claramente objetivo colectivo, carga y foco individual;
  - mostrar consecuencias esperadas en lenguaje futbolístico;
  - las lesiones deben bloquear o adaptar acciones de forma comprensible.
- Preservar contexto al abrir jugador desde plantilla, once o entrenamiento y volver.

**Gate C:** formar un XI, corregir una baja de última hora, cambiar plan táctico y volver a la previa sin perder contexto ni necesitar recargas.

---

## V1.0-D — Día de partido completo

Pantallas principales: previa, `LiveMatchWorkspace`, postpartido.

**Objetivo:** hacer del partido el clímax del bucle, tanto para quien lo juega como para quien pulsa Resultado.

Trabajo:

### Previa

- Dos onces completos en vertical con foto/fallback, dorsal, nombre y posición.
- Escudos, estadio, competición, fecha, árbitro cuando exista y bajas relevantes.
- Diferenciar visualmente `Jugar partido` y `Resultado` sin esconder ninguna opción.
- Resumen táctico legible del rival y de tu propio plan.

### Partido

- Comprobar cronología de eventos y marcador en todo momento.
- Cambios manuales rápidos y seguros.
- Cambios IA realistas por lesión, cansancio, marcador, minutos y posición.
- Evitar sustituciones absurdas, especialmente portero o perfiles incompatibles.
- Tratar correctamente expulsiones, lesión sin cambios, goles tardíos y final de periodo.
- Destacar goles, ocasiones, tarjetas, lesiones, ajustes y cambios; reducir ruido de eventos rutinarios.

### Resultado

- Debe usar el mismo motor, reglas, lesiones, sanciones, cambios, estadísticas y persistencia que un partido jugado.
- Ir al postpartido, no saltar silenciosamente al calendario.

### Postpartido

- Resultado y relato causal antes de tablas detalladas.
- Mejores/peores rendimientos y notas 0–10.
- Eventos y sustituciones verificables.
- Consecuencias visibles: clasificación, lesión, sanción, moral, hitos y reacción del club cuando aplique.
- CTA de salida inequívoco.

**Gate D:** jugar y simular el mismo tipo de fixture producen estructuras persistentes equivalentes y no generan caminos de carrera distintos por errores de integración.

---

## V1.0-E — Mercado, staff y decisiones delegables

Pantallas principales: `MarketWorkspace`, `StaffWorkspace`, `TrainingWorkspace`, áreas de Club/Carrera relacionadas.

**Objetivo:** profundidad tipo manager sin burocracia.

Trabajo:

- Mercado organizado por necesidad de plantilla, no por una base de datos omnisciente.
- Hacer explícito el estado de cada operación: observado → interés → negociación → espera → contraoferta → cerrado/caído.
- Mostrar qué falta para avanzar y quién está esperando a quién.
- Comparar coste deportivo y económico de alternativas A/B/C cuando existan.
- Renovaciones y ofertas entrantes con consecuencias claras.
- Staff: explicar qué aporta cada rol y qué está haciendo ahora.
- La delegación debe reducir clics, no ocultar decisiones críticas.
- Revisión de tiempos y respuestas para evitar cadencias mecánicas repetitivas.
- Toda decisión IA de fichaje relevante debe poder explicarse por necesidad, dinero, entrenador, oportunidad o contexto de plantilla.

**Gate E:** un usuario puede detectar una necesidad, evaluar una alternativa, negociar y entender el desenlace sin consultar varias pantallas desconectadas para reconstruir el proceso.

---

## V1.0-F — Club, competiciones, mundo e historia

Pantallas principales: `ClubWorkspace`, `CompetitionsWorkspace`, `CalendarWorkspace`, `NewsWorkspace`, `HistoryWorkspace`, `ChampionsWorkspace`, `NationalWorkspace`, `CareerWorkspace`, `EconomyWorkspace`.

**Objetivo:** que el mundo sea profundo sin perder legibilidad.

Trabajo:

- Club como “estado del proyecto”: identidad, estadio, clasificación, objetivo, economía, plantilla y presión del consejo.
- Competiciones:
  - formato entendible;
  - clasificación/calendario/cuadro coherentes;
  - campeón y consecuencias archivados correctamente.
- Calendario con jerarquía de próximos hitos, no sólo lista de fechas.
- Noticias: eliminar redundancia; cada noticia debe contar un cambio real o una consecuencia.
- Historial: temporadas, clubes, títulos, premios y partidos memorables navegables.
- Campeones: snapshot histórico inmutable de entrenador/protagonistas para que fichajes posteriores no reescriban el pasado.
- Carrera del mánager: reputación, ofertas, cambios de club y contexto de cada proyecto legibles.
- Economía: explicar tendencia, compromisos y riesgo; evitar presentar contabilidad sin decisión asociada.
- Selecciones: confirmar que convocatorias y torneos respetan la continuidad del mismo universo.

**Gate F:** al acabar una temporada, el usuario puede reconstruir “qué pasó” desde el juego: campeón, clasificación, premios, movimientos y su propia historia.

---

## V1.0-G — Transición de temporada y carrera longitudinal

**Objetivo:** que el juego no sea sólo bueno en agosto de 1993, sino después de muchas temporadas.

Trabajo:

- Pantalla de fin de temporada como hito real.
- Premios, campeón, ascensos/descensos y clasificaciones europeas coherentes.
- Preparación de nueva temporada con checklist breve y accionable.
- Probar mercado, contratos, plantillas, entrenadores, competiciones y economía tras cada transición.
- Confirmar reglas congeladas del universo 1993-94 donde corresponda.
- Verificar que la edad congelada no bloquea evolución deportiva ni genera estados imposibles.
- Detectar acumulación de datos, noticias o decisiones que degraden rendimiento con los años.

**Gate G:** partidas de 3, 10, 20 y 30 temporadas mantienen invariantes del mundo y no presentan corrupción de estado; al menos una partida jugada de forma interactiva debe cruzar dos veranos completos.

---

## V1.0-H — UX visual, responsive, accesibilidad y rendimiento

**Objetivo:** que el juego parezca un producto terminado y no una colección de sistemas funcionales.

Trabajo:

- Auditoría visual de todas las pantallas a 1920×1080.
- Segunda pasada a portátil estrecho y tamaños de texto mayores.
- Jerarquía única de botones, cards, tabs, tablas, chips, banners, estados y modales.
- Evitar héroes enormes, scroll innecesario y controles críticos fuera de pantalla.
- Focus visible y navegación de teclado razonable en controles estándar.
- Contraste y tamaños de texto legibles.
- Skeleton/feedback inmediato en acciones lentas.
- Evitar dobles envíos de botones durante requests.
- Medir cargas de carrera, Continuar, previa, Resultado, postpartido y cambio de temporada.
- Optimizar sólo donde el retraso sea perceptible; no sacrificar claridad por microoptimizaciones.

**Gate H:** ninguna pantalla crítica presenta overflow, controles inaccesibles, textos cortados o una acción importante por debajo de un scroll innecesario en 1080p.

---

## V1.0-I — Robustez destructiva

**Objetivo:** encontrar los bugs que un usuario sí encontrará aunque un test feliz no los vea.

Matriz mínima:

- Back / Forward / F5 en cada workspace crítico.
- Guardar/cargar antes y después de:
  - fichaje;
  - lesión;
  - cambio táctico;
  - inicio de partido;
  - cambio durante partido;
  - final de partido;
  - fin de temporada;
  - cambio de club.
- Doble clic / doble envío en acciones sensibles.
- Red o backend que responde con error en acciones recuperables.
- XI incompleto, lesionado, sancionado y límites reglamentarios.
- Partido con expulsión + lesión + cambios agotados.
- Equipos con plantillas cortas.
- Datos sin foto/escudo/estadio.
- Competición sin siguiente fixture inmediato.
- Usuario despedido durante un periodo con decisiones pendientes.
- Save de una versión anterior razonablemente compatible.

**Gate I:** cero P0 y cero P1 conocidos; cualquier P2 remanente debe tener workaround claro y no afectar integridad de partida.

---

## V1.0-J — Assets históricos en paralelo, con presupuesto limitado

**Objetivo:** seguir enriqueciendo la presentación sin secuestrar el cierre del juego.

Estado del checkpoint de partida:

- escudos reales: **480/504**;
- estadios con foto: **443/504**;
- entrenadores con retrato: **388/426**;
- fotos de jugadores en runtime: **10.195**;
- referencias BDFutbol preparadas cuyo runtime aún no tiene foto: **205**.

Reglas de trabajo:

- El carril de assets nunca bloquea B–I salvo que un recurso roto rompa la UI.
- Presupuesto recomendado: **máximo 10–15 % del esfuerzo de cada pasada** hasta RC.
- Prioridad: club del usuario/próximo rival → ligas jugables → jugadores → entrenadores → estadios → resto del mundo.
- Automatizar descarga, normalización, deduplicación y auditoría siempre que sea fiable.
- Si una fuente no responde, registrar el pendiente y continuar con producto.
- No sustituir un escudo/foto histórica desconocida por una moderna sólo para subir cobertura.
- Mantener fallback bonito y consistente para cualquier hueco.
- Toda incorporación debe conservar fuente/procedencia.

**Gate J:** ningún asset ausente rompe diseño o funcionalidad. La cobertura histórica máxima es deseable, pero el 100 % no es requisito artificial de v1.

---

# Orden real de trabajo

## Ola 1 — Bucle principal

1. B — primeros 15 minutos / Inicio;
2. C — plantilla / jugador / once / táctica;
3. D — previa / partido / Resultado / postpartido;
4. smoke tests de esos recorridos.

Esta ola tiene prioridad absoluta porque es lo que el jugador repite cada jornada.

## Ola 2 — Decisiones de temporada

5. E — mercado / staff / entrenamiento;
6. F — club / competiciones / noticias / historia;
7. navegación contextual entre sistemas.

## Ola 3 — Carrera y fiabilidad

8. G — fin de temporada / nueva temporada / carrera larga;
9. I — ronda destructiva;
10. rendimiento y recuperación de errores.

## Ola 4 — Presentación de release

11. H — pasada visual final en todas las resoluciones objetivo;
12. J — lote corto de assets y revisión de fallbacks;
13. copy final, créditos, versión, packaging y documentación mínima para jugador.

---

# Política de bugs para v1

- **P0:** corrupción de save, bloqueo total, resultado incorrectamente persistido, temporada que no puede continuar, reglas fundamentales rotas. Bloquea inmediatamente.
- **P1:** acción principal inaccesible, navegación que pierde trabajo, incoherencia grave entre sistemas, IA claramente absurda repetible. Bloquea release.
- **P2:** fricción o defecto visual significativo con workaround. Debe intentarse cerrar antes de RC2.
- **P3:** mejora cosmética o profundidad adicional sin impacto en el bucle. Pasa a 1.0.x/1.1.

---

# Gates de release

## Alpha funcional interna

- B–G funcionales.
- Smoke diario verde.
- Se puede completar una temporada interactiva.

## Beta de producto

- H e I ejecutados al menos una vez completos.
- Cero P0.
- P1 sólo si están ya identificados y en corrección inmediata.
- Dos perfiles de usuario: manager veterano y usuario nuevo.

## RC1

- Cero P0/P1 conocidos.
- Dos temporadas interactivas completas con un club.
- Una carrera con cambio de club.
- Simulaciones longitudinales de 3/10/20/30 temporadas verdes en invariantes.
- Build frontend reproducible en entorno de release.

## RC2

- Repetir gates después de todas las correcciones de RC1.
- No introducir features nuevas.
- Sólo bugs, copy, rendimiento y assets de bajo riesgo.

## v1.0.0

Se etiqueta sólo si RC1 y RC2 son consecutivos sin bloqueadores de integridad, navegación o continuidad.

---

# Métricas que sí importan

No usar número de pantallas o assets como métrica de éxito. Para v1 interesa medir:

- tiempo/clics para resolver una decisión frecuente;
- porcentaje de avisos que llevan al destino correcto;
- errores recuperables frente a errores que bloquean carrera;
- estabilidad de save/load;
- coherencia entre Resultado y partido jugado;
- número de decisiones pendientes que realmente requieren intervención;
- frecuencia de sustituciones/decisiones IA absurdas detectadas en muestras;
- tiempo de Continuar y de transición de temporada;
- bugs P0/P1 por sesión de playtest;
- comprensión de pantalla en un usuario nuevo;
- historias que un jugador recuerda tras una temporada.

---

# Estado inicial comprobado en este checkpoint

- Frontend: gates estructurales/UI/sintaxis **28/28 SFC verdes**.
- API/web: **16/16 tests verdes** en la pasada dirigida.
- Partido/contexto/jugabilidad dirigida: **18/18 tests verdes**.
- La suite funcional/longitudinal completa es sensiblemente más lenta y debe mantenerse como gate de release, no como único bucle de desarrollo.
- El `build` de Vite no es reproducible en este entorno actual porque faltan `node_modules`/binario `vite`; esto pasa a ser una tarea de packaging/entorno de release, no un defecto de código demostrado.
- Assets: cobertura elevada pero incompleta; se mantienen como carril paralelo limitado por la política J.
- Primera corrección de Ola 1 aplicada: el directo dispone ahora de un bloqueo común de acciones para impedir dobles avances/simulaciones/cierres/cambios concurrentes; los controles muestran estado de procesamiento y los gates frontend siguen 28/28 verdes.
- Micro-lote de assets intentado (3 referencias): 0 descargas por fallo temporal de resolución DNS de BDFutbol. Se registra el intento y se continúa con producto, tal como exige la política J.

---

# Ejecución B + C + D — Ola 2 cerrada

Esta pasada se ha dedicado íntegramente al bucle diario de juego. **No se ha abierto una pasada seria de assets.**

## B · Inicio

- La acción principal ya depende del estado real: Continuar, Corregir once, Preparar plan o Ir a la previa.
- “Ir a la previa” deja de aparecer como acción válida antes de la fecha del partido.
- Se muestra una banda de preparación con estado del XI, sistema, bajas en el once y fecha del partido.
- Las decisiones y accesos internos pasan por la navegación protegida del flujo de partido.

## C · Plantilla / XI / táctica

- El once distingue claramente LISTO, REVISAR, INCOMPLETO y SIN GUARDAR.
- Los cambios de XI ya no pueden perderse al saltar a Táctica: “Guardar y abrir táctica” sincroniza primero la selección.
- La táctica presenta el recorrido XI → TÁCTICA → PREVIA y sólo habilita la previa en día de partido con un XI legal.
- Si existe una previa a minuto 0, “Revisar XI” la cancela de forma explícita para reconstruir el partido con la nueva selección.
- Cuando el reloj ya ha empezado, Plantilla deja de ser una vía para alterar silenciosamente el equipo del directo: el usuario debe utilizar Cambios.

## D · Día de partido

- La previa a minuto 0 es reversible; un partido ya iniciado no lo es.
- Durante una acción de partido se bloquea también la navegación externa, no sólo los botones del directo.
- Una vez iniciado el reloj, la navegación se concentra en Directo y Táctica/Cambios hasta el final.
- El partido jugado minuto a minuto se compromete automáticamente al llegar a FINAL, igual que “Resultado”; desaparece el estado peligroso de partido terminado pero todavía no persistido.
- El postpartido muestra consecuencias ya aplicadas —posición/puntos, moral, confianza del consejo y siguiente rival— y las mejores notas del equipo.
- Se mantiene un único contrato de cierre para partido jugado y partido simulado.

## Contrato técnico añadido

- Endpoint seguro para cancelar una previa no iniciada: `DELETE /api/football9394/careers/{career_id}/live/preview`.
- `cancel_live_preview()` rechaza la operación si el reloj ya se ha movido.
- `commitFinishedLiveMatch()` unifica la persistencia del final manual con la del resultado instantáneo.
- El gate estático v1.0 protege ahora la continuidad Inicio → XI → Táctica → Previa → Partido → Postpartido y el bloqueo de navegación durante el directo.

## Validación de esta tanda

- Frontend estructural/UI/sintaxis: **28/28 SFC verdes**.
- Smoke específico v1.0: **3/3 verde**.
- Batería dirigida adicional de jornada/previa: **6/6 verde** en la selección ejecutada.
- Las suites longitudinales completas siguen reservadas para gates de release por su duración.
- El build de Vite sigue pendiente de un entorno con dependencias frontend instalables; en este contenedor el binario `vite` no está disponible.

---

# Siguiente tanda recomendada

Mantener el mismo frente antes de volver a recursos gráficos, pero pasar de continuidad funcional a **playtest destructivo de B + C + D**:

1. Inicio: estados vacíos, partido aplazado/sin rival, bajas de última hora y vuelta desde cualquier decisión.
2. Plantilla: sustituciones de XI, disponibilidad, legalidad posicional, navegación ficha → plantilla y vuelta sin pérdida de contexto.
3. Táctica: cambios antes/después de guardar, volver al XI, ajustes en descanso y coherencia entre lo mostrado y lo que consume el motor.
4. Directo: dobles clics, atrás/adelante/F5, descanso, expulsión, lesión, cambios agotados y final de partido.
5. Postpartido: comprobar que clasificación, sanciones, lesiones, moral, noticias y siguiente jornada reflejan exactamente el resultado persistido.
6. Crear smoke tests sólo para los bugs encontrados; no inflar la suite diaria.
7. Assets continúan aparcados salvo recurso roto que perjudique directamente una de estas pantallas.

Sólo después de cerrar esta ronda destructiva conviene abrir una nueva tanda relevante de assets.

---

# Ejecución B + C + D — Ola 3 destructiva cerrada

Esta tanda ha atacado deliberadamente los estados que más fácilmente rompen la confianza del jugador. No se han descargado ni modificado assets.

## Navegación destructiva · F5 / Atrás / Adelante

- La navegación de historial ya no puede escapar de un partido iniciado: con el reloj en marcha sólo se permiten Directo y Táctica/Cambios.
- Una previa todavía en minuto 0 se cancela de forma segura si Atrás/Adelante lleva al usuario a otra sección, evitando dejar un `live_match` fantasma.
- F5 con partido en curso recupera el directo y fuerza una ruta compatible.
- F5 en el postpartido restaura el informe comprometido desde `last_match_report` en vez de mostrar un directo vacío.
- El gate UI de v1.0 protege estos marcadores para que un refactor no reabra silenciosamente el agujero.

## Expulsiones

- Un expulsado deja de aparecer entre los futbolistas sobre el campo que consume la UI.
- El snapshot expone explícitamente `controlled_sent_off` y los IDs expulsados de ambos equipos.
- Una roja deja al equipo con diez; no puede recuperarse la plaza intentando sustituir al expulsado.
- La UI explica que una expulsión no se puede reemplazar.

## Descanso y cambios

- El minuto 45 es un estado estable de descanso, no un minuto normal con botones de avance genéricos.
- La interfaz propone revisar Táctica/Cambios y una acción explícita para comenzar la segunda parte.
- El banquillo muestra cambios usados/restantes con el límite histórico de **2 sustituciones**.
- Al agotar ambos cambios, el tercer cambio queda bloqueado tanto visualmente como en motor/API.
- Los controles de sustitución no aparecen en la previa a minuto 0; un cambio previo al saque inicial debe hacerse desde el XI, no consumiendo una sustitución oficial.

## Lesiones y bajas de última hora

- Se ha probado la baja de entrenamiento sobre un XI ya guardado: si invalida la convocatoria, el asistente la reconstruye legalmente y genera una nota de mánager.
- Una lesión producida durante el directo llega al desarrollo médico, crea noticia y deja al jugador no disponible para el siguiente encuentro.
- El XI persistido queda marcado como inválido si todavía contiene al lesionado, obligando a resolver una situación real en vez de continuar silenciosamente.

## Sanciones longitudinales

Antes de esta ola las amarillas y rojas se contabilizaban en estadísticas, pero no tenían una consecuencia de convocatoria. Queda corregido:

- Cada liga utiliza su `yellow_card_cycle` histórico ya presente en el snapshot; no se introduce un umbral universal inventado.
- Alcanzar el ciclo de amarillas genera un partido de sanción liguera.
- Una expulsión genera también una sanción de un partido de liga.
- El sancionado queda fuera de la construcción automática de XI/banquillo para liga y una selección guardada que lo contenga pasa a ser inválida.
- La ficha/API expone partidos pendientes y motivo de sanción.
- Inicio contabiliza la sanción como baja cuando el siguiente encuentro es de liga.
- Se publica una noticia explicando la sanción.
- La sanción liguera no convierte al jugador artificialmente en inelegible para una copa.
- El partido de sanción se consume al disputar la siguiente jornada de liga y el jugador vuelve a quedar disponible después.

## Cadena postpartido certificada

Se ha añadido un smoke destructivo que comprueba en una misma secuencia:

`resultado comprometido → clasificación actualizada → moral/forma del dashboard → noticias → informe final persistido → siguiente jornada`

El objetivo es evitar que cada pantalla cuente una versión distinta del mismo partido.

## Validación de Ola 3

- Batería destructiva nueva: **7/7 verde**.
- Regresión dirigida previa de core loop + contexto + motor: **10/10 verde**.
- Vue script syntax: **28/28 SFC verdes**.
- SFC structure: **verde**, sin atributos duplicados.
- UI quality gate: **verde**, incluyendo el nuevo contrato destructivo de navegación/incidencias.
- Se intentó una batería combinada más larga incluyendo `test_football9394_manager_career.py`; el entorno agotó el límite de ejecución sin mostrar fallos antes del corte. No se considera un pase completo y se mantiene para el gate largo de release.
- `npm run build` llega correctamente a los tres gates previos pero no puede invocar Vite porque el checkpoint no incluye `node_modules`/binario `vite` en este entorno. No se marca el build como verde.

## Qué queda dentro de B + C + D antes de abandonar este frente

1. Hacer una pasada real de navegador cuando el entorno frontend disponga de Vite/Chromium, reproduciendo F5/Atrás/Adelante y no sólo protegiendo el contrato estático.
2. Romper cambios tácticos en descanso: guardar/no guardar, volver a Directo y comprobar que el motor consume exactamente lo mostrado.
3. Probar segundo amarilla → roja en una secuencia real y lesión con los dos cambios agotados.
4. Probar partido aplazado/sin rival, estado vacío de calendario y final de temporada desde Inicio.
5. Comprobar que sanción/lesión se explican igual en Inicio, Plantilla, ficha, previa, noticia y calendario.
6. Sólo después pasar al siguiente gran bloque de v1.0.0. Los assets siguen como carril secundario y no vuelven a ser frente principal.
