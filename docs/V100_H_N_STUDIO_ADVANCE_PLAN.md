# Míster 93/94 — Plan de avance de estudio V1.0-H → V1.0-N

Fecha de revisión: 18-08-2026  
Punto de partida: **V1.0-G — transición de temporada y carrera longitudinal cerrada**.

**Estado de ejecución (18-08-2026):** antes de H-release hygiene se ha cerrado **H1 — Economía en pesetas** y **H2 — Economía profunda + micro-pasada de assets** por prioridad de producto. La economía separa dato fuente, tesorería, presupuesto de fichajes, reserva operativa y presupuesto salarial; desglosa ingresos/gastos, disciplina deuda/financiación y queda certificada hasta 30 temporadas. Desde H2, cada pasada debe intentar también avanzar assets de forma acotada y auditable. Véanse `docs/V100_H1_ECONOMY_PESETAS.md` y `docs/V100_H2_ECONOMY_DEPTH_ASSET_PASS.md`.

## Decisión de dirección

La base ya no necesita otra expansión horizontal para demostrar profundidad. El siguiente avance debe convertir una simulación muy completa en un **producto terminado, comprensible, estable y agradable de jugar durante cientos de horas**.

La prioridad queda congelada así:

1. **producto ejecutable y releaseable de verdad**;
2. **UX cotidiana y orientación del jugador**;
3. **plantilla/táctica/partido como mejor bucle del juego**;
4. **mercado, staff y entrenamiento como procesos continuos, no pantallas aisladas**;
5. **presentación emocional de partido, títulos, temporadas y carrera**;
6. **refactorización progresiva del frontend/backend sin reescritura destructiva**;
7. **QA humano + destructivo + longitudinal como gate de release**;
8. **assets históricos en paralelo, sin secuestrar el desarrollo**.

No se abre una liga nueva, un 2D ni otro gran sistema hasta superar estos gates.

---

# 1. Qué ha dicho cada mesa de revisión

## Diseño y usabilidad

La interfaz ya tiene una gramática moderna coherente y supera el gate Chromium 1920×1080, pero **“cabe en pantalla” no equivale a “se entiende de inmediato”**. En varias superficies se aprecia densidad alta, mucho microestado simultáneo y una jerarquía que todavía puede pedir demasiado escaneo al usuario.

Prioridades:

- una acción primaria inequívoca por contexto;
- menos competidores visuales dentro de cada panel;
- resumen primero, detalle después;
- diferenciar mejor información, recomendación, alerta y decisión;
- reservar el verde oscuro para identidad/partido y no convertir cada bloque en un panel de mando homogéneo;
- revisar 1366×768, 1600×900 y escalado de Windows 125/150 %, no sólo 1920×1080.

## Expertos en experiencia de usuario

El juego contiene mucha información valiosa, pero la siguiente mejora debe centrarse en **continuidad de tareas**. Cuando una acción atraviesa varios sistemas, el usuario debe saber siempre:

- qué ocurrió;
- quién está trabajando en ello;
- en qué estado está;
- qué falta;
- qué consecuencia puede tener;
- si el usuario debe actuar ahora o puede continuar.

La navegación debe preservar origen, filtros y objeto seleccionado. Las interrupciones de `Continuar` deben ser pocas y justificadas.

## Beta testers / QA

Los mayores riesgos ya no son reglas básicas, sino combinaciones y continuidad:

- F5 / Atrás / Adelante en medio de un proceso;
- doble clic o doble envío durante avances;
- cerrar la aplicación durante guardado/avance;
- save anterior + migración + temporada nueva;
- cambio de club/selección/competición en fechas extremas;
- mercado que cierra durante negociación;
- lesión/sanción/cambio agotado en día de partido;
- verano con múltiples incidencias simultáneas;
- resolución instantánea y partido dirigido produciendo contratos persistentes equivalentes.

La suite tiene mucha profundidad, pero necesita una **pirámide de QA de release** más clara: smoke rápido, integración diaria, destructivo semanal y soak de candidato.

## Jugadores de managers

La petición principal no es “más menús”. Es:

- llegar antes a las decisiones futbolísticas;
- saber por qué el staff recomienda algo;
- cambiar un XI o una táctica en segundos;
- que el partido tenga más tensión y lectura emocional;
- que mercado, lesiones, vestuario y consejo generen historias sin burocracia;
- que ganar una liga, salvarse, descender, cambiar de club o cerrar una temporada se sienta importante;
- que la profundidad avanzada exista, pero no bloquee al jugador que quiere resolver rápido.

## Dirección de estudio

El proyecto entra en **feature freeze de expansión**. Las siguientes fases son de producto, calidad, experiencia y arquitectura. Una feature nueva sólo entra si resuelve una carencia demostrada en el bucle principal.

---

# 2. Hallazgos objetivos del repo que condicionan el plan

## Base longitudinal muy fuerte

V1.0-G certifica 3/10/20/30 temporadas con:

- 444 clubes;
- 0 XI IA ilegales;
- plantillas IA estabilizadas en 20–25 jugadores, mediana 22;
- 0 clubes activos con caja negativa a 30 años;
- historia y honores persistentes;
- save de 33 MB a 30 temporadas;
- rollover maduro en torno a 2 s y temporada madura ~3,4–4,3 s en el entorno de certificación.

Conclusión: el cuello de botella principal **ya no es la supervivencia del mundo**.

## Deuda de release / metadatos

Ahora mismo conviven varias verdades de versión:

- `README.md` abre con V1.0-F aunque G está cerrado;
- `project_football9394.json` sigue en `0.51.0-nf9-nf12-professional-world`;
- `frontend/package.json` sigue en `0.28.0`;
- FastAPI declara `version="0.8.0"`.

Esto debe desaparecer antes de un RC. La versión tiene que tener **una única fuente canónica**.

## Build y distribución aún no son un gate verde

Los gates SFC/UI/Vue pasan, pero el `vite build` de producción no está certificado en este ZIP. El script raíz arranca el backend, mientras frontend y backend siguen siendo pasos separados de desarrollo.

Para considerar la v1 un producto distribuible hace falta certificar:

- build frontend real;
- integración frontend/backend de producción;
- empaquetado de escritorio si ése es el canal de entrega;
- directorio de datos/save del usuario;
- actualización/migración segura;
- logs recuperables y diagnóstico de crash.

## Riesgo de mantenibilidad

Puntos de concentración actuales:

- `manager_career.py`: ~306 KB, 193 funciones/métodos detectados;
- `Football9394App.vue`: ~1.100 líneas, más de 100 `ref`, decenas de operaciones async;
- `webapp.py`: 88 endpoints en un único módulo;
- `football9394-manager.css`: ~168 KB.

No son fallos funcionales, pero sí aumentan el coste y el riesgo de cada nueva mejora. La respuesta debe ser **extracción progresiva con tests de caracterización**, nunca una reescritura total.

## Documentación con verdad histórica mezclada con verdad actual

Hay 55 documentos Markdown y numerosos cierres válidos como archivo histórico, pero README/MASTER/planes antiguos todavía contienen estados “activos” ya superados. Hace falta separar:

- documentación canónica actual;
- arquitectura;
- QA/release;
- historial de checkpoints archivado.

## Assets: buena cobertura, huecos concretos

El audit actual registra:

- 480/504 escudos de clubes reales presentes; 24 faltantes;
- 443 fotos de estadio presentes; 61 huecos de equipos;
- 388/426 fotos de entrenadores; 38 faltantes;
- 10.195 fotos de jugador en disco;
- 205 fotos de jugador ya preparadas por fuente pero todavía ausentes en runtime.

Es un carril paralelo de alto retorno visual, pero no debe bloquear H–N.

---

# 3. Plan canónico V1.0-H → V1.0-N

## V1.0-H — Release hygiene, documentación y suelo técnico

### Objetivo

Conseguir que el repo tenga una sola verdad de producto y pueda producir un candidato ejecutable reproducible.

### Trabajo

1. Crear `VERSION` o manifiesto equivalente como fuente única.
2. Derivar desde él:
   - versión API;
   - versión frontend;
   - versión visible en UI;
   - checkpoint/release metadata.
3. Actualizar README al estado G real.
4. Crear documentación canónica mínima:
   - `docs/STATUS.md`;
   - `docs/ROADMAP.md`;
   - `docs/ARCHITECTURE.md`;
   - `docs/QA_RELEASE.md`.
5. Mover planes/cierres históricos no canónicos a `docs/archive/` sin perderlos.
6. Certificar `npm ci` + `npm run build` en entorno de release.
7. Definir launcher de producción único.
8. Definir ubicación de saves, copias de seguridad y logs.
9. Añadir guardado atómico: temporal → fsync/validación → replace.
10. Añadir recuperación del último save válido y diagnóstico legible.

### Gate H

- una sola versión visible en repo/API/frontend;
- `npm run build` PASS real;
- arranque de producción con una sola acción;
- crear carrera → guardar → cerrar proceso → abrir → continuar PASS;
- corrupción/truncado intencionado de save no destruye el último backup válido;
- README describe únicamente el estado actual y enlaza el histórico.

---

## V1.0-I — UX cotidiana: Inicio, Continuar y procesos legibles

### Objetivo

Que jugar una semana sea más fácil que navegar por el juego.

### Trabajo

1. Rehacer la prioridad de Inicio alrededor de cuatro bloques:
   - **Ahora**: qué requiere acción;
   - **Próximo partido**;
   - **Qué cambió desde la última pausa**;
   - **Pulso del club**.
2. Agrupar múltiples avisos de una misma causa.
3. Cada interrupción explica por qué ha detenido `Continuar`.
4. Cada tarjeta de proceso muestra:
   - estado;
   - responsable;
   - siguiente paso;
   - fecha/espera estimada cuando aplique;
   - CTA principal.
5. “Resolver y volver” conserva el punto de origen.
6. Persistir filtros, pestaña, scroll lógico y selección relevante en pantallas de trabajo.
7. Añadir breadcrumbs/contexto sólo donde ayuden; no duplicar navegación.
8. Reducir clics de acciones frecuentes.
9. Añadir búsqueda rápida de jugador/club/competición si los playtests demuestran que el sidebar ya no basta.
10. Crear microcopy uniforme para `pendiente`, `en curso`, `esperando`, `bloqueado`, `resuelto`.

### Gate I

Playtest ciego con usuarios que no conocen el código:

- iniciar carrera y llegar al primer partido sin instrucciones externas;
- localizar la siguiente decisión en ≤10 s en al menos 90 % de escenarios preparados;
- decisiones obligatorias habituales en ≤3 clics desde Inicio;
- ningún tester pierde el contexto tras resolver una incidencia;
- ninguna interrupción de Continuar carece de causa y acción explícitas.

---

## V1.0-J — Plantilla, XI, táctica y partido: el corazón del producto

### Objetivo

Hacer que preparar y vivir un partido sea la parte más satisfactoria del juego.

### Plantilla / XI

- campo más protagonista y menos “tabla con panel auxiliar”;
- clic jugador → posiciones compatibles;
- clic posición → candidatos válidos;
- cambio campo↔banquillo directo;
- condición, forma, sanción, lesión, moral y encaje legibles sin abrir ficha;
- explicación local de ilegalidad del XI;
- atajos `mejor XI`, `último XI`, `rotar cansados` como opciones, no automatismos obligatorios;
- mantener retorno exacto al cerrar ficha de jugador.

### Táctica

- capa 1: intención del plan en lenguaje futbolístico;
- capa 2: órdenes principales;
- capa 3: detalle experto/individual;
- mostrar consecuencias esperables y conflictos reales;
- presets editables y comparación “qué cambia respecto al plan actual”;
- en directo, sólo mostrar ajustes relevantes al contexto del marcador/minuto.

### Previa

- dos XI verticales completos con retrato/fallback, dorsal, posición y estado;
- rival, entrenador, estadio, árbitro, bajas y scouting integrados sin competir visualmente;
- `Jugar partido` y `Resultado` con jerarquía equivalente pero intención distinta;
- última comprobación de XI/táctica sin pasos redundantes.

### Directo

- narración más editorial y menos parecida a log técnico;
- ritmo visual para gol, ocasión, tarjeta, lesión, descanso, cambio y final;
- controles de velocidad y filtro de relato si todavía no están en el flujo final;
- sustitución rápida desde el banquillo;
- recomendación del staff accionable con comparación antes/después;
- estados críticos —roja, lesión sin cambios, remontada, final apretado— visualmente inequívocos.

### Postpartido

- primero: qué pasó y por qué;
- después: quién decidió el partido;
- luego: consecuencias ya aplicadas;
- finalmente: estadísticas y detalle;
- enlace directo a clasificación/noticia/lesión/sanción afectada.

### Gate J

- usuario nuevo forma XI legal, cambia un jugador y guarda sin explicación externa;
- lesión de última hora se corrige desde la misma cadena de contexto;
- un ajuste táctico en descanso se aplica y se refleja en relato/diagnóstico;
- `Resultado` y partido dirigido comparten persistencia y consecuencias;
- 10 partidos seguidos jugados por testers sin incidencia P0/P1 y con valoración subjetiva del flujo de partido ≥8/10 de media.

---

## V1.0-K — Mercado, staff, scouting, médico y entrenamiento como procesos únicos

### Objetivo

Eliminar la sensación de “saltar entre departamentos” para completar una sola decisión.

### Mercado

Representar cada objetivo como una línea temporal:

`necesidad → búsqueda → seguimiento → informe → consulta → negociación → decisión → incorporación/fracaso → consecuencia`.

Mostrar en el mismo contexto:

- por qué interesa;
- qué sabemos y con qué confianza;
- quién está trabajando;
- coste probable;
- alternativas A/B/C;
- impacto salarial/de plantilla;
- competencia real;
- siguiente fecha relevante.

### Staff / delegación

- responsabilidades explicadas por efecto, no por título;
- cambiar responsable muestra qué procesos activos se ven afectados;
- carga de trabajo visible y comprensible;
- delegación permite jugar rápido sin ocultar consecuencias importantes;
- el staff recomienda, pero no sustituye al usuario en decisiones que éste haya retenido.

### Médico

- una sola verdad de disponibilidad entre Inicio, Plantilla, ficha, XI, previa y noticias;
- diagnóstico, intervalo, riesgo, recomendación y evolución con lenguaje consistente;
- diferenciar dato observado de estimación.

### Entrenamiento

- objetivo semanal antes que cuadrícula de parámetros;
- carga de equipo y riesgo de individuos visibles;
- sugerencias de recuperación accionables;
- relación clara entre preparación de partido, familiaridad, fatiga y riesgo.

### Gate K

Cinco recorridos completos deben poder seguirse sin perder el objeto ni el estado:

1. fichaje normal;
2. negociación aplazada/contraoferta;
3. mercado cerrado durante proceso;
4. lesión relevante con recomendación médica;
5. cambio de responsable con trabajo ya abierto.

En todos ellos el usuario sabe siempre `qué pasa / quién actúa / qué falta / qué debo hacer`.

---

## V1.0-L — Presentación emocional, historia y recompensa

### Objetivo

Que la carrera sea recordable, no sólo correcta.

### Trabajo

- pantalla de campeón realmente celebratoria;
- fin de temporada con jerarquía narrativa;
- resumen de temporada del club y del mánager;
- premios y XI de la temporada más visuales;
- récords y hitos contextualizados;
- rivalidades y reencuentros reaparecen en previa/noticia/postpartido cuando son relevantes;
- cambio de club, destitución, ascenso, descenso y regreso reciben una presentación proporcional;
- verano: briefing editorial, prioridades y calendario de decisiones;
- historial permite reconstruir una temporada sin leer bases de datos;
- “momentos de carrera” guardables/favoritos sólo si aporta valor real en playtest.

### Gate L

Tras 3 temporadas, un tester puede responder desde el propio juego:

- qué ganó;
- cuál fue su mejor/peor temporada;
- qué jugadores fueron importantes;
- qué rivalidades/hitos recuerda;
- por qué cambió de club o proyecto;
- cómo quedó cada temporada archivada.

Sin consultar ficheros externos ni logs técnicos.

---

## V1.0-M — Refactorización controlada y rendimiento de producto

### Objetivo

Reducir el coste de mantener el juego sin alterar su comportamiento.

### Regla

**No reescritura.** Cada extracción empieza con tests de caracterización y termina con el mismo contrato observable.

### Backend

Dividir `manager_career.py` gradualmente en dominios:

- `career_state.py` / migraciones;
- `career_matchday.py`;
- `career_rollover.py`;
- `career_market.py`;
- `career_economy.py`;
- `career_manager_jobs.py`;
- `career_history.py`;
- `career_club_context.py`.

Dividir `webapp.py` en routers:

- career;
- match;
- squad/tactics/training;
- market/scouting;
- club/staff/board;
- competitions/history;
- national/world.

Añadir contratos tipados para payloads de dominio donde todavía circulen `dict` ambiguos.

### Frontend

Extraer de `Football9394App.vue`:

- `useCareerState`;
- `useNavigationContext`;
- `useMatchday`;
- `useSquadSelection`;
- `useMarketFlow`;
- `useSeasonHistory`;
- `useAsyncActionLock`.

Separar CSS en:

- tokens;
- shell/layout;
- componentes base;
- workspaces;
- responsive/accessibility.

### Rendimiento

Medir, no suponer:

- arranque;
- carga de carrera;
- cambio de workspace;
- apertura de ficha;
- guardado;
- Continuar día normal;
- rollover;
- memoria frontend tras 60 min de sesión.

### Gate M

- ningún cambio funcional intencionado durante extracción;
- suites de caracterización verdes antes/después;
- reducción clara del tamaño/responsabilidad del root app y runtime principal;
- no regresión de los tiempos G;
- ningún endpoint pierde compatibilidad sin migración/versionado explícito.

---

## V1.0-N — Beta final, accesibilidad, empaquetado y Release Candidates

### Objetivo

Cerrar una versión que pueda jugarse, instalarse y recuperarse como producto.

### Matriz de prueba visual

- 1920×1080 @100 %;
- 1600×900 @100 %;
- 1366×768 @100 %;
- 1920×1080 @125 % de escalado;
- 1920×1080 @150 % de escalado;
- teclado completo en acciones principales;
- foco visible;
- contraste y estados disabled/error/selected;
- modales en viewport reducido.

### Matriz destructiva

- F5/Atrás/Adelante en cada workspace;
- doble click/doble submit;
- cambio de vista durante petición lenta;
- cierre durante guardado;
- save viejo y migraciones encadenadas;
- save 10/20/30 temporadas;
- mercado y rollover el mismo día;
- cambio de club + selección;
- partido aplazado/sin rival/fixture raro;
- lesión + expulsión + cambios agotados;
- temporada sin premios/movimientos esperados;
- assets ausentes;
- red/API caída o respuesta fallida durante acción no idempotente.

### Beta humana

Perfiles mínimos:

- usuario nuevo;
- jugador de Football Manager;
- jugador de PC Fútbol/manager clásico;
- jugador que simula casi todos los partidos;
- jugador que dirige todos;
- jugador de sesiones largas;
- usuario de club grande;
- usuario de club modesto/inferior;
- carrera de selección;
- carrera con cambios de club.

Registrar:

- dónde se atasca;
- tiempo hasta entender una pantalla;
- clics;
- errores de interpretación;
- acciones que esperaba y no encontró;
- pantallas que ignora;
- valoración 0–10 de Inicio, Plantilla, Táctica, Partido, Mercado, Temporada y experiencia global.

### Release gate

**RC1** sólo sale con 0 P0 conocidos.  
**RC2** sólo sale después de corregir P1 de RC1 y repetir el soak/recorridos críticos.  
**v1.0.0** sólo se etiqueta si RC1 y RC2 consecutivos no introducen nuevos P0 y los P1 restantes están explícitamente aceptados como deuda no bloqueante.

---

# 4. Carril paralelo de assets

No se convierte en frente principal. **Regla transversal desde H2:** cada pasada de desarrollo debe ejecutar al menos un microintento de assets, con límite pequeño, procedencia registrada y resultado auditable. Si la red o la fuente falla, el checkpoint principal no se bloquea: se registra el fallo y se continúa. El comando canónico es `python backend/tools/run_asset_pass.py --limit 12 --report <ruta.json>`.

Orden recomendado:

1. 24 escudos reales faltantes;
2. 205 retratos de jugador ya preparados por fuente pero aún no presentes en runtime;
3. 38 entrenadores sin retrato;
4. 61 estadios sin foto;
5. después, huecos individuales de jugador por prioridad de uso real.

Priorizar siempre:

- club del usuario;
- próximo rival;
- ligas jugables;
- jugadores/entrenadores que aparecen en pantallas principales.

Nunca inventar una imagen histórica. Mantener procedencia y fallback digno.

---

# 5. Qué NO haría ahora

Hasta cerrar H–N:

- no abrir más ligas por volumen;
- no crear un 2D complejo;
- no rehacer el motor de partido desde cero;
- no añadir otra capa de relaciones/memoria sólo por profundidad;
- no perseguir 100 % de fotografías antes de cerrar UX;
- no rediseñar todo el frontend otra vez;
- no reescribir `manager_career.py` de una sola vez;
- no añadir burocracia porque “Football Manager la tiene”.

Cada nueva propuesta debe responder: **¿mejora una decisión, una historia o la claridad del jugador?** Si no, va a post‑v1.

---

# 6. Orden recomendado de ejecución

1. **H — release hygiene + build + saves + docs**.
2. **I — Inicio/Continuar/procesos y navegación contextual**.
3. **J — Plantilla/XI/Táctica/Partido**.
4. **K — Mercado/Staff/Scouting/Médico/Entrenamiento**.
5. **L — Presentación emocional e historia**.
6. **M — refactorización progresiva**, iniciada técnicamente en paralelo desde H pero sin bloquear los playtests.
7. **N — beta final + empaquetado + RC1/RC2**.
8. Assets continúan en segundo plano con presupuesto fijo.

---

# 7. Definition of Done global

Míster 93/94 queda preparado para v1.0.0 cuando:

- se instala/arranca como producto sin montar un entorno de desarrollo;
- el usuario puede iniciar, guardar, cerrar, recuperar y continuar una carrera de forma segura;
- Inicio le explica qué requiere atención;
- las decisiones habituales se resuelven con pocas acciones y retorno contextual;
- plantilla, XI y táctica son rápidos y legibles;
- previa, partido, Resultado y postpartido forman una sola experiencia coherente;
- mercado/staff/médico/entrenamiento presentan procesos, responsables, estados y consecuencias;
- títulos, fin de temporada y cambios de carrera se sienten como acontecimientos;
- 30 temporadas siguen sanas después de todos los cambios de producto;
- la build de producción y el empaquetado están certificados;
- la documentación tiene una sola verdad actual;
- RC1 y RC2 pasan sin P0 y sin regresiones críticas.

La meta ya no es demostrar que el juego tiene muchas cosas. La meta es que **todo lo que ya tiene se sienta conectado, comprensible, fiable y divertido de usar**.
