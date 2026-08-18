# Míster 93/94 v1.1.0 — Auditoría UX/UI integral y pasada de producto seria

**Fecha:** 18-08-2026  
**Base:** `1.0.0-m-refactor-progressive-closed`  
**Referencia de auditoría:** `docs/reference/AUDITORIA_UX_SERIOUS_RELEASE_SOURCE.txt`  
**Benchmark interno revisado:** BasketManager v1.1.0 UX source checkpoint (`docs/current/V1_1_0_UX_AUDIT_AND_REDESIGN.md`, `PLAN_V1_1_0_UX_20260818.md` y primitivas `Ui*`).  
**Objetivo:** elevar Míster desde un v1 funcional a un producto que se entiende, se recorre y se disfruta como juego de gestión, sin borrar profundidad ni reescribir reglas cerradas.

> Principio rector: **situación → por qué importa → responsable → alternativas → decisión → ejecución/espera → consecuencia → memoria**.

## Alcance y evidencia

Se ha inspeccionado el shell Vue, los 24 workspaces/componentes del dominio `football9394`, las capas CSS, los composables de navegación/estado/locks, los 88 contratos API de fútbol, la documentación canónica, los tests de cierre A–M, las capturas D9 a 1920×1080 y el checkpoint UX de BasketManager.

Las capturas D9 son útiles como evidencia histórica de problemas de jerarquía y uso del espacio, pero **no certifican el render actual**: son anteriores a la pasada oscura V1.0-I y a esta v1.1.0. El gate visual actual debe regenerarse con Chromium y dependencias frontend completas antes de RC.

No se ha alterado la lógica deportiva ni el save schema. La pasada se concentra en arquitectura de información, continuidad de decisiones, componentes, estados, persistencia, microcopy y contratos automáticos.

---

# A. Diagnóstico ejecutivo

1. **Míster ya tiene un producto real debajo de la UI.** Inicio, plantilla, táctica, partido, mercado, staff, entrenamiento, economía, carrera e historia están conectados a sistemas con consecuencias; el problema principal ya no es amplitud funcional, sino conseguir que el usuario perciba esa profundidad como una experiencia continua.
2. **La fantasía correcta es “estoy al mando de un club de 1993-94”, no “consulto una base de datos histórica”.** La UI debe convertir datos en situaciones, responsables, decisiones y consecuencias.
3. **Inicio es una buena base de centro operativo.** Ya eleva próximo partido, preparación, decisiones, procesos, noticias y tabla. Debe mantenerse como “qué necesita mi atención ahora”, evitando añadir más KPIs por inercia.
4. **La navegación técnica era sólida pero la arquitectura mental estaba demasiado agrupada.** `GESTIÓN` y `CLUB Y MUNDO` mezclaban intenciones distintas. Se reorganiza en `HOY`, `EQUIPO`, `CLUB`, `TEMPORADA` y `CARRERA Y MUNDO`.
5. **F5/Atrás/Adelante ya son una fortaleza y deben tratarse como contrato de producto.** `useNavigationContext.js` protege previa/directo, historial y hash; no se rediseña, se blinda.
6. **Faltaba acceso directo experto.** Se incorpora un “Ir a…” global mediante Ctrl/Cmd+K para evitar memorizar rutas o recorrer el lateral.
7. **Las decisiones de Inicio podían perder contexto al llevar al usuario a otra pantalla.** Se incorpora `DecisionFocusBar`: asunto, contexto, siguiente paso, consecuencia de esperar y retorno al origen permanecen visibles mientras se resuelve.
8. **Las pantallas principales tenían soluciones visuales repetidas pero no un contrato común.** Se introducen `UiPageHeader`, `UiActionDock`, `UiProcessTrail`, `UiEmptyState` y `UiDataTable`.
9. **Plantilla es una de las superficies más maduras funcionalmente.** Tiene XI + cinco suplentes, drag & drop, disponibilidad, ficha, filtros y acciones; su mayor fricción de uso repetido era perder filtros/orden al salir. Se persisten en `sessionStorage`.
10. **Tácticas tenía profundidad, pero necesitaba un siguiente paso inequívoco.** La preparación XI → táctica → previa y el descanso usan ahora trail + dock de acción, preservando explícitamente “Plan para la 2ª parte”.
11. **Mercado es el mejor ejemplo futbolístico para adoptar la disciplina de BasketManager.** Ya posee necesidad, scouting, comparación A/B/C, negociación y presupuesto; se normaliza la representación del proceso y se hace explícito el coste/espacio restante antes de comprometerse.
12. **Staff y entrenamiento no deben ser pantallas administrativas.** La clave es saber quién trabaja, con qué calidad/carga, qué está pendiente y qué cambia. Se unifican cabeceras, estados y continuidad de entrenamiento.
13. **Los estados vacíos eran demasiado textuales.** Calendario, Noticias, Competiciones y Carrera pasan de “no hay” a explicar por qué, si es normal y qué hará que cambie.
14. **Las capturas D9 evidencian el riesgo histórico de “SaaS claro + mucho espacio muerto”.** El dark pass actual corrige dirección artística, pero necesita nueva evidencia runtime para validar densidad, contraste y primer viewport.
15. **El design system actual ya tiene identidad suficiente.** Fondo azul noche, paneles profundos, azul de acción, verde/gold/red semánticos, fotos/escudos y césped dan personalidad. No hace falta otra skin.
16. **El mayor riesgo técnico transversal sigue siendo `Football9394App.vue`.** Tras M queda en ~68 KB / 1.139 líneas: está bajo el gate de M, pero sigue concentrando orquestación. La v1.1 no debe volver a meter lógica de UI transversal ahí.
17. **El CSS está mejor estructurado, pero aún es denso.** Las capas `depth.css`, `workspaces.css`, `shell.css` y `product.css` concentran muchos contratos. Las nuevas primitivas deben reducir excepciones al tocar cada flujo, no provocar una reescritura masiva.
18. **No se detecta un P0 estático nuevo en esta pasada.** El principal bloqueo para declarar RC no es una funcionalidad ausente, sino completar browser/visual/playtest con el render actual y cerrar los P1 que salgan de ahí.
19. **BasketManager aporta principios, no una apariencia a copiar.** Lo útil es su disciplina de ActionDock, ProcessTrail, empty/error canónicos, foco de decisión, navegación persistente y gates UX.
20. **La prioridad de v1.1.0 es claramente experiencia, no features.** La pasada ya transforma superficies frecuentes y deja un gate automático para evitar que futuras iteraciones reviertan estos contratos.

---

# B. Problemas críticos

| Prioridad | Ubicación | Problema / evidencia | Impacto en el jugador | Propuesta | Estado |
|---|---|---|---|---|---|
| P1 | Shell / decisiones | Al salir de una decisión de Inicio se perdía el hilo contextual | Puede llegar a Mercado/Plantilla/Táctica y olvidar qué estaba resolviendo | `DecisionFocusBar` persistente hasta cerrar/volver | Implementado base |
| P1 | Arquitectura información | `GESTIÓN` y `CLUB Y MUNDO` agrupaban intenciones distintas | Más exploración y memorización del lateral | HOY / EQUIPO / CLUB / TEMPORADA / CARRERA Y MUNDO | Implementado |
| P1 | Navegación experta | No existía acceso directo global | Usuarios veteranos recorren lateral repetidamente | Ctrl/Cmd+K + “Ir a…” | Implementado |
| P1 | Workspaces multipaso | Cabeceras, pasos y CTAs se resolvían de forma ad hoc | Cada pantalla exige reaprender jerarquía | PageHeader + ProcessTrail + ActionDock | Implementado en núcleo |
| P1 | Plantilla | Filtros y orden locales se perdían al desmontar pantalla | Repetición de trabajo en una pantalla de alta frecuencia | Persistencia de vista en sesión | Implementado |
| P1 | Release UX | No hay captura/browser actual posterior a dark pass + v1.1 | No se puede certificar contraste, viewport, scroll y foco sólo desde source | Chromium visual matrix + playtest | Abierto RC |
| P2 | Estados vacíos | Mensajes “no hay” sin causa/acción en varias superficies | Duda sobre si es normal, bug o falta de datos | `UiEmptyState` explicativo | Implementado en núcleo; expandir |
| P2 | Tablas | Algunas tablas siguen HTML directo y con densidad variable | Scroll/lectura inconsistentes | `UiDataTable` por tareas de alta frecuencia | Parcial |
| P2 | Entidades relacionadas | No todas las menciones de club/jugador/partido/noticia son navegables | Se rompe la continuidad narrativa | Contrato `EntityLink` futbolístico | Abierto |
| P2 | Noticias | La noticia explica hecho, pero no siempre ofrece protagonista/acción contextual | Hemeroteca puede sentirse pasiva | noticia → protagonista → contexto → acción | Abierto |
| P2 | Calendario | Lista contextual clara, pero un partido histórico/futuro no tiene ruta de detalle genérica desde la fila | Se pierde navegación natural por entidad partido | ficha/preview de partido navegable | Abierto |
| P2 | `Football9394App.vue` | ~1.139 líneas / 68 KB | Cambios transversales pueden reintroducir acoplamiento | seguir extracción por caso de uso | Abierto progresivo |
| P2 | CSS | capas grandes, estilos legacy y feature rules conviven | riesgo de excepciones visuales | migración al tocar flujo + contratos | Abierto progresivo |
| P2 | Onboarding | Producto profundo sin guía contextual sistemática | nuevo jugador tarda en descubrir prioridades | ayudas de primera vez no bloqueantes | Abierto |
| P3 | Command palette | búsqueda por texto y Enter al primer resultado; sin navegación ↑↓ dedicada | experto de teclado pierde velocidad fina | roving selection + flechas | Abierto |
| P3 | Fichas | ficha jugador es rica, otras entidades no siempre comparten misma jerarquía | lectura diferente según entidad | cabecera estable + resumen + tabs por intención | Parcial |
| P3 | Microcopy | quedan acciones cortas válidas por contexto, pero no hay checker semántico exhaustivo | pequeñas dudas repetitivas | verbo + objeto cuando la consecuencia importa | Continuo |
| P3 | Responsive | CSS contempla 1180/900/700, pero falta evidencia real actual | riesgo en 1366/1280/1024 y zoom | matriz visual | Abierto RC |
| P4 | Hitos | tratamientos especiales ya existen, pero pueden ganar mejor navegación cruzada | emoción sin suficiente reentrada histórica | hito → temporada/equipo/jugador | Futuro |

### Clasificación mantener / pulir / reorganizar / rediseñar / sustituir / eliminar

- **Mantener:** motor, reglas, F5/Back/Forward, bucle de partido, Inicio como centro operativo, ficha jugador, XI drag & drop, mercado A/B/C, historia/hitos.
- **Pulir:** microcopy, densidad de tablas, navegación teclado, responsive, entidades clicables.
- **Reorganizar:** navegación global y jerarquía de cabeceras/acciones.
- **Rediseñar:** estados vacíos, representación de procesos, continuidad de decisiones entre pantallas.
- **Sustituir:** patrones ad hoc de cabecera/proceso/CTA por primitivas compartidas al tocar cada flujo.
- **Eliminar:** confirmaciones rutinarias o wrappers visuales que no añadan información; no se detecta en esta pasada una funcionalidad de juego que deba eliminarse.

---

# C. Nueva dirección UX

Míster debe sentirse como **la mesa de trabajo de un entrenador-mánager de fútbol en un mundo histórico vivo**.

La pantalla no empieza por “qué datos tengo”, sino por cinco preguntas:

1. ¿Dónde estoy?
2. ¿Qué está pasando?
3. ¿Qué requiere atención?
4. ¿Qué puedo hacer ahora?
5. ¿Qué cambiará después?

Reglas globales:

- Nivel 1: bloqueo/decisión/partido próximo.
- Nivel 2: información necesaria para elegir.
- Nivel 3: contexto y tendencia.
- Nivel 4: detalle histórico/analítico bajo demanda.
- Un proceso largo siempre muestra dueño, estado, siguiente paso y consecuencia.
- Una decisión que abre otra pantalla conserva su asunto de origen.
- Una operación frecuente evita modal de confirmación; una destructiva sí explica impacto.
- Inicio no duplica todo: prioriza y enlaza.
- La profundidad se revela por capas, no se esconde.
- El jugador experto dispone de acceso directo y persistencia; el nuevo recibe contexto y estados explicativos.

---

# D. Nueva dirección visual

## Identidad

**Nocturna, futbolística, editorial y de club.** Histórica en contenido —fotos, escudos, estadios, nombres, reglas—, moderna en interacción. No imitar software de 1993 ni dashboard corporativo.

## Paleta canónica actual

La capa oscura vigente define:

- fondo: `#07111d`;
- panel principal: `#0d1825`;
- panel secundario: `#111e2c`;
- texto: `#eef4fb`;
- texto secundario: `#93a3b5`;
- acción: `#2d79e6`;
- éxito/disponibilidad: `#43c985`;
- hito/advertencia: `#e0b64f`;
- peligro: `#e46868`;
- información: `#4b92f1`.

El color nunca debe ser el único portador de estado; texto, icono/label y estructura deben acompañarlo.

## Tipografía y densidad

- familia: Inter / system UI;
- suelo de texto funcional compartido: 11 px;
- títulos de pantalla: 22 px en `UiPageHeader`;
- densidad media-alta, pero con separación por decisiones y no por “tarjetas para todo”;
- tablas contenidas con sticky header donde aporten trabajo real.

## Componentes

- `UiPageHeader`: ubicación, propósito, estado y acciones de cabecera.
- `UiActionDock`: qué haces ahora + por qué + qué pasará.
- `UiProcessTrail`: etapas, actual, completadas y responsable/contexto.
- `UiEmptyState`: causa + normalidad + próximo paso.
- `UiDataTable`: tabla de trabajo contenida, focalizable y sticky.
- `DecisionFocusBar`: contexto longitudinal de una decisión iniciada en Inicio.
- `ManagerCommandPalette`: acceso experto directo.

## Imágenes

Fotos, escudos y estadios refuerzan identidad y orientación. No deben ser requisito para comprender una acción. Los fallback tienen que conservar tamaño y jerarquía.

## Momentos especiales

Reservar tratamientos más espectaculares para título, ascenso/descenso, fin de temporada, récord, gran fichaje y partido decisivo. El día a día debe ser sobrio para que esos hitos pesen.

---

# E. Arquitectura de información propuesta

## Navegación primaria v1.1

**HOY**
- Inicio

**EQUIPO**
- Plantilla
- Tácticas
- Entrenamiento

**CLUB**
- Mercado
- Cuerpo técnico
- Economía
- Club

**TEMPORADA**
- Competiciones
- Calendario
- Noticias

**CARRERA Y MUNDO**
- Carrera
- Selecciones
- Historia
- Campeones

Esta agrupación responde a intención, no a módulo técnico.

## Navegación secundaria

- Ctrl/Cmd+K abre “Ir a…”.
- Atrás/Adelante preservan el contrato de `useNavigationContext`.
- Hash válido permite reentrada/F5 en sección segura.
- Un asunto iniciado en Inicio conserva `DecisionFocusBar` al saltar a otro workspace.

## Siguiente escalón de arquitectura

Introducir navegación cruzada uniforme:

- jugador → ficha;
- club → club;
- competición → competición + pestaña;
- partido → previa/directo/post según estado;
- lesión → jugador + contexto médico;
- noticia → protagonista;
- operación de mercado → jugador + club + caso activo.

No se fuerza todavía un router nuevo: debe construirse sobre el contrato hash existente o mediante una transición caracterizada.

---

# F. Flujos principales

## F1. Día normal

Inicio → prioridad dominante → destino → acción → feedback → consecuencia → retorno a Inicio → Continuar.

**v1.1:** la decisión mantiene contexto mediante `DecisionFocusBar`.

## F2. Plantilla / convocatoria

Necesidad → filtrar plantilla → XI → cinco suplentes → revisar bajas/reglas → guardar → abrir Táctica → previa.

**v1.1:** filtros/orden persisten durante la sesión; `UiActionDock` declara si la convocatoria está incompleta, sin guardar o lista.

## F3. Táctica / partido

XI guardado → plan → encaje de perfiles → órdenes → previa → jugar/simular → descanso → ajuste → final → consecuencias.

**v1.1:** `UiProcessTrail` + dock; descanso mantiene “Plan para la 2ª parte” y retorno al partido.

## F4. Mercado

Necesidad → responsable/scouting → evidencia → shortlist → A/B/C → oferta → espera/contraoferta → resolución → coste → plantilla/noticia.

**v1.1:** proceso normalizado, estados vacíos explicativos y coste restante visible antes de ofertar; “Aceptar oferta” evita microcopy ambigua.

## F5. Staff

Área → responsabilidad → responsable → informe/trabajo → decisión → efecto.

**v1.1:** PageHeader y EmptyState; “Ir al área” sustituye lenguaje genérico.

## F6. Entrenamiento / médico

Necesidad → responsable → trabajo semanal → sesión → carga/condición/riesgo → recomendación → siguiente sesión/partido.

**v1.1:** `UiProcessTrail` explícito y ActionDock para cambios pendientes/guardados.

## F7. Calendario / competición

Calendario → partido/estado → competición → clasificación/resultados/calendario/palmarés → siguiente evento.

**v1.1:** estados entre fases explican normalidad y siguiente paso; tabla de clasificación usa contenedor canónico.

## F8. Carrera

Reputación → vacante → candidatura → entrevista/oferta → aceptar/rechazar → cambio de club → memoria/relación.

**v1.1:** estado vacío de vacantes explica por qué no hay y qué hará cambiar el mercado.

## F9. Historia y emoción

Hecho → capítulo/hito → reaparición contextual → palmarés/temporada → futura rivalidad/cambio de club.

Ya existe base L. El siguiente trabajo es reforzar navegación desde el hito hacia sus entidades sin convertir cada evento en una cinemática.

---

# G. Rediseño pantalla por pantalla

## Inicio

**Mantener:** hero de próximo partido, preparación, decisiones, procesos, cambios recientes, nombres del momento, tabla, noticias.  
**Problema:** riesgo de pérdida de contexto al saltar.  
**v1.1:** decisiones emiten objeto completo; `DecisionFocusBar` acompaña la resolución.  
**Siguiente:** dedupe de señales y test con 0/1/20 pendientes.

## Plantilla

**Problema:** alta densidad y filtros efímeros.  
**v1.1:** PageHeader; DataTable; EmptyState; ActionDock; filtros/orden persistentes; XI + banquillo continúan drag & drop.  
**Jerarquía:** estado convocatoria → lista de trabajo → campo/banquillo → consecuencias.  
**Siguiente:** persistir scroll/selección de jugador cuando se abra/cierre ficha.

## Tácticas

**Problema:** profundidad sin contrato común de proceso/CTA.  
**v1.1:** PageHeader + ProcessTrail + ActionDock; continuidad descanso/directo.  
**Siguiente:** hacer que cambios importantes resuman trade-off antes de aplicar.

## Mercado

**Problema:** flujo potente pero podía percibirse como varias cajas.  
**v1.1:** PageHeader; ProcessTrail; A/B/C preservado; EmptyState; ActionDock con presupuesto restante.  
**Siguiente:** navegación de caso/entidades y persistencia del caso activo vía URL/estado.

## Cuerpo técnico

**Problema:** lenguaje de área administrativa.  
**v1.1:** cabecera común, empty state explicativo, microcopy “Ir al área”.  
**Siguiente:** representar cambio de responsable con before/after de calidad/carga.

## Entrenamiento

**Problema:** responsable, proceso y guardado competían visualmente.  
**v1.1:** PageHeader con responsable, continuidad, trail, ActionDock; los cambios sin guardar son explícitos.  
**Siguiente:** navegación directa desde riesgo médico a ficha/jugador cuando exista ruta contextual.

## Calendario

**Problema:** tabla artesanal y empty state poco orientador.  
**v1.1:** PageHeader + DataTable + EmptyState; ritmo/mercado permanecen como rail.  
**Siguiente:** partido clicable y restauración de posición al volver.

## Competiciones

**Problema:** “sin tabla”, “sin resultados” o “sin partidos” podían parecer ausencia de datos.  
**v1.1:** PageHeader con selector; DataTable en clasificación; estados vacíos con explicación de formato/fase.  
**Siguiente:** entidad equipo/partido clicable y árbol/estructura de eliminatorias más navegable.

## Noticias

**Problema:** buena causalidad, poca acción contextual.  
**v1.1:** PageHeader + EmptyState narrativo; se mantiene cadena causal y mundo técnico.  
**Siguiente:** protagonista clicable + volver a hemeroteca conservando categoría/scroll.

## Carrera

**Problema:** vacante vacía podía interpretarse como sistema sin actividad.  
**v1.1:** PageHeader; EmptyState explica compatibilidad/reputación/mercado.  
**Siguiente:** comparación de proyectos A/B cuando coincidan ofertas.

## Partido

**Mantener:** previa con XI, Resultado/Jugar, directo, descanso, expulsión, lesión, límite de cambios, postpartido y cadena de consecuencias.  
**Siguiente:** visual regression actual, foco/teclado y CTA sin scroll a 1920×1080/1366×768.

## Club / Historia / Campeones / Economía / Selecciones

Tienen ya trabajo reciente y no se rediseñan “porque sí”. Se mantienen y se incorporarán primitivas únicamente cuando un test o flujo demuestre una inconsistencia real. Prioridad: navegación cruzada, estados y uso de espacio.

---

# H. Design System

## Contrato de uso

| Componente | Usar cuando | No usar para |
|---|---|---|
| `UiPageHeader` | Cada workspace necesita ubicación, propósito, estado y acciones | tarjetas internas |
| `UiActionDock` | Existe una decisión/siguiente paso dominante | acciones menores de fila |
| `UiProcessTrail` | Un flujo tiene etapas/esperas/responsable | una lista plana de estados independientes |
| `UiEmptyState` | No hay contenido y el usuario necesita entender por qué | errores técnicos (requieren ErrorState) |
| `UiDataTable` | Tabla de trabajo con scroll/sticky/foco | layouts de tarjetas |
| `DecisionFocusBar` | El usuario salió de Inicio para resolver un asunto | navegación normal sin caso activo |
| `ManagerCommandPalette` | acceso global experto | buscador de entidades todavía no implementado |

## Reglas

- Texto funcional compartido ≥11 px.
- Focus visible en componentes interactivos.
- `prefers-reduced-motion` respetado.
- Disabled debe ser visual y semántico.
- Error ≠ empty state.
- Una acción principal por bloque decisional.
- Sticky sólo si reduce scroll y no tapa contenido.
- No usar color como único indicador.
- No inventar tarjetas para agrupar contenido que ya tiene jerarquía.

---

# I. Plan de implementación

## UX-0 — Auditoría viva + contratos · BASE CERRADA

**Objetivo:** que UX importante sea verificable en source.  
**Cambios:** nuevas primitivas, `check:ux`, legibilidad ≥11 px, reduce motion/focus.  
**Aceptación:** `check:sfc`, `check:ui`, `check:ux`, `check:vue` verdes.  
**Riesgo:** bajo.

## UX-1 — Shell + arquitectura mental · BASE CERRADA

**Objetivo:** saber dónde estoy y llegar rápido.  
**Cambios:** grupos HOY/EQUIPO/CLUB/TEMPORADA/CARRERA Y MUNDO; Ctrl/Cmd+K.  
**Pruebas:** Back/Forward/F5, teclado, viewport.  
**Pendiente:** flechas en palette y browser visual.

## UX-2 — Inicio + continuidad de decisión · BASE CERRADA

**Objetivo:** Inicio → asunto → resolución → retorno.  
**Cambios:** `DecisionFocusBar`.  
**Aceptación:** asunto no se pierde al abrir workspace.  
**Pendiente:** playtest 0/1/20 pendientes.

## UX-3 — Plantilla / táctica / entrenamiento · BASE CERRADA

**Objetivo:** trabajo diario continuo.  
**Cambios:** primitivas, filtros persistentes, trails y docks.  
**Pendiente:** scroll/selección al volver de ficha, browser drag&drop.

## UX-4 — Mercado / staff como caso continuo · BASE CERRADA PARCIAL

**Objetivo:** necesidad → responsable → decisión → consecuencia.  
**Cambios:** trail, comparación preservada, coste de oportunidad, microcopy.  
**Pendiente:** caso serializable en navegación y entity links.

## UX-5 — Calendario / competiciones / noticias / carrera · BASE CERRADA PARCIAL

**Objetivo:** estados explicables y navegación natural.  
**Cambios:** headers/data tables/empty states.  
**Pendiente:** entidad partido/noticia/club clicable y retorno con contexto.

## UX-6 — Fichas y navegación de entidades · SIGUIENTE P1/P2

**Objetivo:** cualquier entidad relevante se abre desde donde aparece.  
**Técnico:** extender contrato de navegación sin romper hash/F5.  
**Aceptación:** noticia→jugador→Atrás conserva hemeroteca; partido→detalle→Atrás conserva calendario; jugador anterior/siguiente desde listas cuando tenga sentido.

## UX-7 — Estados / feedback / errores · SIGUIENTE P2

**Objetivo:** ninguna acción deja duda.  
**Aceptación:** >500 ms con feedback; retry localizado; lenguaje de usuario; empty/error diferenciados.  
**Pruebas:** timeout, offline, respuesta vacía, doble click, recarga durante acción.

## UX-8 — Onboarding contextual + experto · SIGUIENTE P2/P3

**Objetivo:** primera decisión interesante <10 min sin tutorial largo.  
**Cambios:** ayudas contextuales una vez; atajos; palette mejorada; quizá recientes/favoritos si el playtest demuestra valor.

## UX-9 — Accesibilidad / responsive / visual · BLOQUE RC

**Objetivo:** certificar render real.  
**Matriz:** 1920×1080, 1366×768, 1280×720/800, 1024×768, 200 % zoom.  
**Aceptación:** sin CTA crítica inaccesible, sin scroll horizontal de página, foco visible, modales dentro de viewport.

## UX-10 — Playtest + RC · BLOQUE FINAL

**Sesiones:** 15 min nuevo, 1 h intermedio, varias horas, experto, destructivo.  
**Métricas:** clics/tarea, tiempo, retrocesos, errores, abandono, tiempo a primera decisión, funciones ignoradas.  
**Gate:** source + backend focal + browser/visual + jornada + mercado + transición temporada + soak.

---

# J. Matriz de prioridades

| Cambio | Impacto | Frecuencia | Esfuerzo | Riesgo | Prioridad | Estado |
|---|---:|---:|---:|---:|---|---|
| Contexto de decisión entre pantallas | Muy alto | Alta | Medio | Bajo | P1 | Hecho |
| Reorganizar navegación | Alto | Muy alta | Bajo | Bajo | P1 | Hecho |
| Command palette | Alto experto | Alta | Bajo | Bajo | P1 | Hecho |
| Persistir filtros Plantilla | Alto | Muy alta | Bajo | Bajo | P1 | Hecho |
| Primitivas PageHeader/ActionDock/Trail | Muy alto | Alta | Medio | Medio | P1 | Hecho base |
| Empty states explicativos | Alto | Media | Bajo | Bajo | P2 | Hecho núcleo |
| Entity navigation universal | Muy alto | Alta | Alto | Medio | P2 | Pendiente |
| Browser visual current-state | Muy alto | Release | Medio | Bajo | P1 RC | Pendiente |
| Onboarding contextual | Alto nuevos | Baja por usuario | Medio | Bajo | P2 | Pendiente |
| Palette flechas/recent | Medio | Media experto | Bajo | Bajo | P3 | Pendiente |
| CSS/App extracción adicional | Medio indirecto | Continua | Alto | Medio | P2 técnico | Progresivo |
| Nuevas features horizontales | Bajo v1.1 | Variable | Alto | Alto | P4 | No priorizar |

---

# K. Plan de pruebas

## Source gates

- `npm run check:sfc`
- `npm run check:ui`
- `npm run check:ux`
- `npm run check:vue`
- `npm run check:version`
- `python backend/tools/sync_product_version.py --check`

## Backend focal

- M refactor contract.
- core loop.
- management continuity.
- destructive matchday por casos: roja, descanso, límite de cambios, lesión previa, sanción, cadena postpartido, lesión en vivo.

## Browser / destructivo

1. F5 en Inicio, Plantilla, Táctica, Mercado, Previa y Directo.
2. Atrás/Adelante tras abrir una decisión.
3. Plantilla: filtrar/ordenar → otra sección → volver.
4. Plantilla: drag starter↔starter; banquillo 5/5; baja de última hora.
5. Táctica: guardar → previa; descanso → aplicar → volver.
6. Mercado: necesidad → A/B/C → oferta → espera/contraoferta/cierre.
7. Calendario: vacío, aplazado/sin rival, muchas filas.
8. Noticias: 0, 1, 30 noticias; textos largos.
9. Competiciones: liga, copa sin tabla única, finalizada, entre fases.
10. Carrera: con club, sin club, 0 vacantes, varias ofertas.
11. Error API/timeout/doble click.
12. 1920/1366/1280/1024 + 200 %.

## Playtest personas

**A — nuevo:** riesgo principal = entender qué hacer después de crear carrera. Medir primera decisión y primera previa.  
**B — conoce el género:** riesgo = jerarquía/terminología propia. Medir búsqueda de convocatoria, mercado y staff.  
**C — hardcore:** riesgo = demasiada UI narrativa. Medir velocidad con filtros/atajos.  
**D — rápido/teclado:** riesgo = palette todavía básica. Medir clics y teclado.  
**E — comete errores/usa Atrás:** riesgo = pérdida de contexto. Medir restauración de estado.

## Test de 5 segundos

Pantallas objetivo: Inicio, Plantilla, Táctica, Mercado, Previa, Directo, Post, Calendario, Carrera. Deben identificar ubicación, situación, foco y acción primaria.

## Test de 3 clics / interacciones razonables

- Inicio → resolver decisión.
- Plantilla → ficha jugador.
- Plantilla → guardar XI → táctica.
- Táctica → previa.
- Inicio → mercado → objetivo.
- Calendario → competición.

No es regla rígida; cualquier excepción debe aportar contexto real.

---

# L. Definition of Done v1.1.0 UX / Release Candidate

La revisión se considera terminada cuando:

1. La acción principal de cada pantalla core puede identificarse en <5 s en playtest.
2. Inicio muestra una prioridad clara y no duplica el mismo bloqueo de forma confusa.
3. Una decisión iniciada en Inicio conserva contexto al navegar a su destino.
4. Back/Forward/F5 conservan una ruta segura y el contexto soportado.
5. Plantilla conserva filtro/orden durante la sesión y no pierde convocatoria sin avisar.
6. XI completo = 11 + 5; drag & drop y reglas de disponibilidad siguen operativos.
7. Táctica mantiene continuidad XI → táctica → previa y descanso → 2ª parte.
8. Mercado muestra necesidad, responsable, evidencia/estado, siguiente paso y coste antes de comprometerse.
9. Entrenamiento/staff hacen visible responsable, estado, próximo paso y consecuencia.
10. Ningún empty state core se limita a “No hay datos”.
11. Una operación >500 ms muestra feedback en runtime.
12. Los errores se explican en lenguaje de jugador y ofrecen recuperación cuando exista.
13. Ningún modal crítico excede el viewport objetivo.
14. No hay scroll horizontal de página a 1920×1080; tablas pueden tener scroll contenido cuando sea necesario.
15. Ningún CTA crítico queda fuera del primer viewport sin una razón de diseño explícita.
16. Texto funcional de primitivas compartidas ≥11 px.
17. Foco visible y navegación de teclado funcionan en shell, palette y acciones core.
18. La información no depende únicamente de rojo/verde/amarillo.
19. Entidades principales tienen navegación cruzada suficiente para los flujos priorizados o una deuda P1 explícita antes de RC.
20. Los hitos especiales conservan tratamiento emocional sin convertir el día a día en una sucesión de cinemáticas.
21. `check:sfc`, `check:ui`, `check:ux`, `check:vue` y `check:version` están verdes.
22. Contratos backend focales de partido/gestión/refactor están verdes.
23. Chromium visual regression actual se regenera y revisa en 1920×1080 y viewports secundarios.
24. Playtest de nuevo/intermedio/experto/destructivo no descubre P0; los P1 restantes son finitos, documentados y con responsable/criterio de cierre.
25. La release se reproduce desde repo limpio y no altera reglas deportivas por un rediseño visual.

---

# Cambios aplicados en esta pasada

- nuevas primitivas en `frontend/src/components/ui/`;
- nueva capa `frontend/src/styles/football9394-primitives.css`;
- `DecisionFocusBar.vue` y `ManagerCommandPalette.vue`;
- `ManagerTopbar.vue` con “Ir a…” y contexto de sección;
- `Football9394App.vue` con continuidad de decisión y palette;
- nueva arquitectura de `navigationGroups`;
- Plantilla: PageHeader, DataTable, EmptyState, ActionDock y persistencia de filtros/orden;
- Táctica: PageHeader, ProcessTrail y ActionDock;
- Mercado: PageHeader, ProcessTrail, EmptyState y ActionDock;
- Staff: PageHeader, EmptyState y microcopy de destino;
- Entrenamiento: PageHeader, ProcessTrail y ActionDock;
- Calendario: PageHeader, DataTable y EmptyState;
- Competiciones: PageHeader, DataTable y EmptyState contextual;
- Noticias: PageHeader y EmptyState narrativo;
- Carrera: PageHeader y EmptyState de mercado de banquillos;
- `frontend/tools/ux-product-contract.mjs` + script `npm run check:ux` integrado en build;
- micro-pasada paralela de assets documentada en `docs/v110_ux_asset_microbatch_attempt.json`.

# Benchmark BasketManager: qué se adapta y qué no

Se adaptan **principios**: foco de decisión, process trail común, action dock, empty state explicativo, tabla de trabajo, navegación persistente y contratos UX automatizados.

No se copia su IA de navegación, taxonomía de baloncesto, roles deportivos, composición visual concreta ni reglas de producto. En Míster los procesos se traducen al fútbol 93/94: convocatoria 11+5, táctica de fútbol, scouting/fichajes, cuerpo técnico, carga, sanciones, partido y carrera histórica.

# Limitaciones conocidas de esta evidencia

- El build Vite completo y el screenshot browser actual requieren `node_modules`/Chromium disponibles; `npm ci` no pudo completarse en este entorno en la primera tentativa.
- Las capturas D9 del repo son previas a la UI oscura actual y por tanto no deben usarse como certificación final.
- El bloque pytest destructivo completo excede la ventana si se ejecuta monolíticamente; los casos se validan segmentados y el timeout nunca se contabiliza como pase.
- No se declara v1.1.0 RC final hasta cerrar browser/visual/playtest.

---

# Addendum v1.1.1 — cierre source UX-4 / UX-5 / UX-6 (18-08-2026)

La continuación consolidada en v1.1.1 convierte tres deudas del informe en contratos source verificables sin declarar todavía RC visual.

## UX-4 — Navegación de entidades · SOURCE CERRADO BASE

- `useNavigationContext.js` conserva entidad, profundidad de historial y pestaña de ficha de jugador (`entityTab`).
- Back/Forward/F5 reconstruyen el contexto soportado desde URL/history.
- `ManagerTopbar` expone un retorno visible cuando existe contexto anterior.
- Noticias enlaza jugador, club y competición cuando el evento aporta entidad.
- Los errores de carga de entidad ya no destruyen la ruta: permiten **Reintentar** o **Volver**.

**Pendiente RC:** ejecutar el flujo completo en Chromium y comprobar restauración visual de filtros, pestaña, scroll y selección donde proceda.

## UX-5 — Feedback/error/runtime · SOURCE CERRADO BASE

- feedback visible de operación lenta a partir de 500 ms;
- timeout a 15 s con copy orientada al jugador;
- sanitización de errores técnicos (`null`, `undefined`, exception/500 equivalentes);
- colapso de mutaciones idénticas concurrentes para reducir dobles envíos por doble click;
- EmptyState y ErrorState quedan semánticamente separados;
- error de entidad con recuperación localizada.

**Pendiente RC:** provocar offline, timeout, respuesta inválida y doble click en browser real y observar comportamiento, foco y recuperación.

## UX-6 — Onboarding contextual + experto · SOURCE CERRADO BASE

- `FirstRunGuide` aparece en la primera carrera antes del primer partido dirigido y puede descartarse;
- guía prioridad → convocatoria 11+5 → consecuencias, sin tutorial lineal largo;
- command palette mantiene Ctrl/Cmd+K y añade navegación por flechas, selección activa y Enter;
- la ayuda deja de ocupar el flujo una vez que el usuario ha empezado realmente a jugar.

**Pendiente RC:** playtest de usuario nuevo para medir tiempo a primera decisión y sesión experta para medir coste de navegación.

## Evidencia actual

- frontend version/SFC/UI/UX/Vue: PASS; Vue 38/38;
- backend H release: 7/7;
- J: 4/4; K: 6/6; L: 6/6; M: 5/5 por invocaciones separadas;
- `vite build` no certificable porque el entorno carece del binario `vite` y no puede completar `npm ci` por DNS;
- suites que muestran casos y luego exceden la ventana se documentan como timeout, nunca como pase completo.

La prioridad pasa por tanto a **UX-7 Visual/responsive/accesibilidad** y **UX-8 Playtest**, no a abrir nuevas funcionalidades.


---

# Addendum — v1.1.1 navegación de entidades + refactor de shell (18-08-2026)

La segunda continuación convierte la navegación cruzada en una capacidad de producto con seam técnico propio y mantiene intacto el cierre progresivo M.

## Cambios cerrados en source

- nuevo `useEntityNavigation.js`: carga, sincronización, retry y restauración de jugador/club/competición/partido fuera del root;
- `useFirstRunGuide.js` y `useManagerShortcuts.js` separan onboarding y velocidad experta del shell;
- `entityPresentation.js` concentra la traducción del calendario a lenguaje de jugador;
- `Football9394App.vue` baja a 69.607 bytes y vuelve a cumplir el límite de caracterización `<70.000`;
- endpoint de club contextual en carrera incorporado al contrato HTTP M;
- la ficha de club rival conserva incertidumbre: no expone `overall` exacto cuando scouting no lo conoce;
- Calendario, Competiciones y Noticias pueden seguir naturalmente hacia club, partido, jugador o competición;
- la pestaña de ficha de jugador sigue representada en URL/history; los fallos de carga ofrecen Reintentar/Volver.

## Gates de esta continuación

- frontend `check:version`, `check:sfc`, `check:ui`, `check:ux`, `check:vue`: PASS;
- M refactor: 5/5;
- I funcional: 4/4 (el único test excluido es el sentinel histórico que exige literalmente `1.0.0-i`);
- J: 4/4, segmentado por coste; K: 6/6; L: 6/6;
- core loop + management continuity: 5/5;
- endpoint/ficha de club + incertidumbre: 2/2.

## Límite RC que permanece abierto

No se certifica todavía `vite build` ni Chromium actual. El entorno no dispone de los paquetes npm necesarios y la instalación no puede completar las descargas por resolución DNS. El siguiente trabajo canónico sigue siendo UX-7/UX-8: browser real, matriz responsive/accesibilidad y playtest.

---

# Addendum v1.1.2 — RC browser contracts (18-08-2026)

La pasada v1.1.2 mueve UX-4/UX-5/UX-7 desde “source diseñado” a **contratos ejecutables** sin falsear el último salto de producción.

- Chromium source-CSS: 8/8 viewports/zoom equivalentes.
- History API Chromium: 9/9 para serialización de ruta, entidad, pestaña, Atrás, Adelante y remount.
- Network contract: 10/10 para doble envío, feedback lento, offline, timeout y 500 sanitizado.
- `navigationRoute.js` y `requestTransport.js` reducen responsabilidad de composables/API y hacen testeables los contratos críticos.
- Se corrige un bug real de barra móvil/200 %: la navegación deja de aparecer por encima de la topbar y queda fija abajo en una sola fila.
- `Saltar al contenido` pasa a un patrón de ocultación visual compatible con navegación de teclado.
- `rc_production_browser_gate.py` define el DoD técnico del bundle: carrera nueva, responsive, Ctrl+K, Plantilla/Mercado, Back/Forward y F5 literal.
- Backend: H 7/7, M 5/5; carrera 14/14 por ejecuciones segmentadas, incluidos dos rollovers longitudinales.

La build sigue **no certificada** porque `vite`/`frontend/dist` no están disponibles en este entorno. Este bloqueo se conserva explícito como P1 de release, no se sustituye por la harness visual.
