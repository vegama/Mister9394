# Míster 93/94

## Estado · checkpoint 0.51.0-nf9-nf12-professional-world

La pasada **NF9→NF12** conecta cuatro capas que ya comparten realidad: **carrera profesional, consejo/proyecto, mundo informativo causal y economía longitudinal**. El entrenador puede buscar empleo, presentar candidatura, pasar entrevista, firmar en otra liga sin resetear el mundo, recibir ofertas con contrato vigente o dimitir conservando reputación, relaciones y memoria. El consejo mantiene objetivos, filosofía y márgenes de proyecto, puede exigir una venta por una crisis real y resuelve peticiones con condiciones y memoria anti-exploit. Véase `docs/V051_NF9_NF12_PROFESSIONAL_WORLD.md` y `docs/FM_REFERENCE_FUNCTIONAL_PLAN.md`.

La prensa deja de ser un feed aislado: consultas, negociaciones, fichajes, candidaturas y decisiones del consejo forman hilos `hecho → rumor → noticia → reacción → consecuencia`; un rumor no confirmado se enfría sin transformarse mágicamente en verdad. La economía longitudinal clasifica los flujos reales ya movidos por el motor —taquilla, comercial, salarios, mercado, deuda y premios— sin duplicar caja, conserva temporadas y conecta crisis, presión de venta y cambios estructurales como ascensos/descensos.

Validación de cierre: **81/81 backend PASS** en los grupos seleccionados NF9–NF12, web/API, NF3–NF8, movilidad, economía, v0.49, v0.48, NF0 staff, mercado y F1–F8. Frontend: **SFC/UI/Vue PASS 26/26**. `vite build` no se certifica porque el binario Vite no está materializado en este entorno; los prechecks anteriores a Vite sí pasan.

## Estado · checkpoint 0.50.0-nf3-nf8-functional-depth

La pasada **NF3→NF8** convierte entrenamiento, táctica, staff, vestuario, mercado y partido en un flujo funcional conectado. NF3 añade recuperación individual y preparación específica; NF4 incorpora fases tácticas persistentes, familiaridad, órdenes individuales/rival y lanzadores con efectos reales en el motor; NF5 genera informes de staff con autor/confianza/evidencia/acción; NF6 abre preocupaciones causales, respuestas y disciplina; NF7 profundiza consulta/negociación/rol/prima/cláusula y añade cesiones completas; NF8 conecta briefing, consejo/rendimiento en vivo, ajustes inmediatos y diagnóstico postpartido. Véase `docs/V050_NF3_NF8_FUNCTIONAL_DEPTH.md` y el plan rector `docs/FM_REFERENCE_FUNCTIONAL_PLAN.md`.

La cesión ya recorre el ciclo **negociación → plantilla → contrato temporal → promesa/noticia/reacción → devolución automática al club de origen**. Los roles prometidos en fichajes no se pierden al firmar y el vestuario los juzga mediante selecciones reales. Los cambios de fase táctica hechos durante el directo se sincronizan con el estado vivo del motor.

Validación seleccionada: **71/71 backend PASS** (11 nuevas NF3–NF8 + 44 regresión funcional/motor/mercado/vestuario/F1–F8 + 16 web/API). Frontend: **SFC/UI/Vue PASS 25/25**. El fichero pesado `test_football9394_manager_career.py` no se recertifica: supera la ventana de ejecución tras cinco casos sin fallo, por lo que no se infiere un PASS. `vite build` tampoco se certifica porque el binario Vite no está materializado en este entorno.

## Estado · checkpoint 0.49.0-training-load-scouting-capacity-flow

La nueva pasada conecta varias funciones a la vez: **entrenamiento semanal, carga/fatiga/condición, riesgo médico, capacidad de scouting, geografía y envejecimiento de informes**, además de enlazar las necesidades del planificador directamente con el mercado. El usuario ya puede editar intensidad/sesiones/focos individuales desde la nueva superficie **Entrenamiento** y esas decisiones alteran estado real del jugador.

El scouting ya no admite encargos infinitos: la capacidad depende de la estructura de staff, los desplazamientos añaden tiempo y los informes pierden confianza/precisión con los meses. Una lesión sufrida entrenando queda integrada con medicina/noticias y, si invalida una convocatoria guardada, el juego la repara de forma segura o explica que falta plantilla. Véase `docs/V049_TRAINING_LOAD_SCOUTING_CAPACITY_FLOW.md`.

Regresión seleccionada: **85/85 pruebas ejecutadas PASS** en los grupos NF0/NF1/NF2/NF3, desarrollo, mercado, motor, F1–F8, M4–M14, gate M15 de cuatro perfiles, API y movilidad. El gate M15 de tres temporadas excede 180 s y se marca explícitamente como **no recertificado**, no como PASS. Frontend: **SFC/UI/Vue PASS 25/25**. `vite build` sigue sin certificarse porque el binario Vite no está materializado en este entorno.

## Estado · checkpoint 0.48.0-functional-scouting-planning-staff-effects

La nueva etapa **NF0–NF3** ya ha dejado de ser sólo infraestructura. La delegación del cuerpo técnico tiene consecuencias operativas y alimenta una primera vertical jugable de scouting, planificación de plantilla, medicina e informe del rival. El plan rector sigue en `docs/FM_REFERENCE_FUNCTIONAL_PLAN.md`.

El mercado de jugadores externos ya no revela automáticamente la verdad del motor: muestra estimaciones y rangos según conocimiento persistente, permite encargar informes que tardan días y registra responsable/confianza. El planificador expone al usuario la misma lógica de necesidades que usa la IA, incluyendo cobertura, contratos, sucesión y excedentes. El área médica comunica intervalos y recomendaciones a través del responsable sanitario, y el análisis del rival limita la información táctica según la calidad del informe. Las negociaciones registran quién las dirige y su competencia tiene efectos moderados en tiempos y exigencias. Véase `docs/V048_FUNCTIONAL_SCOUTING_PLANNING_STAFF_EFFECTS.md`.

Regresión seleccionada: **44/44 backend verdes** (30 del lote funcional/API/NF0/partido/mercado + 14 F1–F8) y gates frontend **SFC/UI/Vue PASS 24/24**. El `vite build` no se certifica en este entorno porque el binario Vite no está materializado; todos los gates previos sí pasan.

## Estado · checkpoint 0.47.0-nf0-staff-responsibilities-base

Se abre la nueva etapa de **profundidad funcional NF0–NF12**, inspirada en la filosofía de Football Manager pero adaptada a Míster 93/94. El plan rector queda guardado en `docs/FM_REFERENCE_FUNCTIONAL_PLAN.md`.

NF0 ya tiene una primera vertical real: cuerpo técnico persistente por club, empleados generados claramente etiquetados cuando no existe fuente histórica individual, competencias funcionales, carga de trabajo y nueve responsabilidades que el usuario puede asumir o delegar sólo en personal elegible. La nueva superficie **Cuerpo técnico** está conectada a API y guardado; cambiar una responsabilidad persiste. Tests dedicados NF0 5/5, regresión API 16/16, movilidad afectada 2/2 y gates frontend SFC/UI/Vue PASS. NF0 sigue abierto: el siguiente paso es hacer que estas responsabilidades modifiquen información y resultados reales de scouting, médico, entrenamiento y mercado. Véase `docs/V047_NF0_STAFF_RESPONSIBILITIES_BASE.md`.

## Estado · checkpoint 0.40.0-belgium-antwerp-germinal-beveren-molenbeek-deep

Bélgica sigue **abierta**. Después de profundizar Royal Antwerp, Germinal Ekeren, Beveren y Molenbeek, los huecos belgas bajan de 275→**183** fechas de nacimiento y de 248→**169** nacionalidades internacionales; también se reducen país de nacimiento 268→194, altura 322→262 y peso 369→330. La pasada corrige posiciones inferidas, separa homónimos (Steve/Michael Laeremans), conserva Estados históricos como Zaire cuando corresponde y documenta conflictos en lugar de inventar precisión. La regresión específica v0.36-v0.40 + identidad queda 26/26 PASS.

Rusia no se abre todavía: antes se continúa por Genk, Waregem, Lommel y el resto de clubes belgas pendientes. La futura pasada rusa deberá tratar URSS/ex-URSS con política histórica explícita de ciudadanía, lugar de nacimiento, selección, transliteraciones y Estados sucesores. Ver `docs/V040_BELGIUM_ANTWERP_GERMINAL_BEVEREN_MOLENBEEK_DEEP.md`.

Manager de fútbol histórico centrado en la temporada 1993-94 y en carreras persistentes multitemporada.


## Estado · checkpoint 0.34.0-turkey-altay-ankaragucu-kayserispor-deep

La 0.34 retoma el punto real de la rama: **0.33**, con Gaziantepspor ya cerrado, y profundiza Altay, Ankaragücü y Kayserispor **27/27 cada uno**. Se revisan 81 perfiles (74 nuevas profundizaciones respecto a 0.33), se ejecutan 48 correcciones funcionales de rol y el acumulado turco único de esta fase llega a 269 perfiles.

Los huecos turcos bajan de 194 a **124 fechas de nacimiento** y de 193 a **121 nacionalidades internacionales**; el país de nacimiento pendiente cae de 323 a 259. Hay 31 perfiles con especialidad posicional corroborada y 50 donde la fuente sólo demuestra una línea amplia. Estos 50 se marcan deliberadamente `exact role unresolved`: el aumento de `profile_review_required` de 30 a 80 significa más honestidad de datos, no una regresión. Dos nacimientos sólo documentan el año y se mantienen sin día/mes inventado.

Se incorporan **15 retratos BDFutbol nuevos**, normalizados y comprobados físicamente a JPEG RGB 40×55; el acumulado sube de 54 a **69**. Las 81 biografías afectadas se regeneran en el campo canónico 1993-94 y ya no convierten una posición amplia en una especialidad por la redacción. Registro y cola conservan 2.107 IDs únicos y sincronizados.

Quedan documentados los conflictos de fecha de Öztürk Tanrıbilir (se prioriza la ficha oficial TFF: 03/05/1966) y Sergei Yevgenovich Gusev (01/07/1967 por corroboración de varias fuentes frente al 07/07 de BDFutbol). Los nacidos en estados disueltos conservan el lugar histórico textual sin fabricar un país moderno de nacimiento.

La regresión histórica seleccionada queda en **80/80 pruebas verdes**, con el bloque específico 0.34 en **6/6**. La suite completa del repositorio no se declara ejecutada. Véase `docs/V034_TURKEY_ALTAY_ANKARAGUCU_KAYSERISPOR_DEEP.md`.

## Estado · checkpoint 0.33.0-turkey-gaziantep-next-profiles

La 0.33 continúa la profundización turca sin abrir frentes nuevos. **Gaziantepspor queda curado 26/26** con identidad completa, fecha de nacimiento, nacionalidad internacional, lugar de nacimiento, ficha BDFutbol y posición respaldada por fuente; cuando sólo puede demostrarse `Defender`, `Midfielder` o `Forward`, la especialización exacta queda marcada como pendiente. Se añaden además siete perfiles de alta confianza de Altay, Ankaragücü y el Kayserispor histórico.

Esta pasada profundiza **33 perfiles** y ejecuta **24 correcciones funcionales de rol**. El acumulado turco de la fase queda en **195 perfiles curados y 120 correcciones posicionales**. Turquía mantiene 419 jugadores activos, pero reduce los huecos de 227 a **194 fechas de nacimiento** y de 226 a **193 nacionalidades internacionales**. Los ocho nuevos casos de posición amplia elevan `profile_review_required` de 22 a 30 de forma deliberada: el dato incierto se conserva como incierto.

Se incorporan **18 retratos BDFutbol nuevos**, normalizados físicamente a JPEG RGB 40×55, y el total empaquetado sube de 36 a **54**. Las 1.813 biografías activas se vuelven a regenerar después de las correcciones; 33 cambian respecto a 0.32 y no queda ningún jugador reconstruido sin fila de staging. Registro y cola de fotos continúan con 2.107 identidades únicas y sincronizadas.

Entre los arreglos de mayor impacto están Kubilay Toptaş a delantero centro, Kemal Sönmez a central, Hasan Çelik a delantero centro, Tayfun Yungul a mediocentro, Yuriy Matveev a delantero centro, Öztürk Tanrıbilir a portero y Cafer Aydın a delantero centro. En nacidos en la antigua URSS se conserva el lugar histórico en texto y no se fuerza un `birth_country_id` moderno. No se usa ninguna regla 75/25 en fútbol.

La regresión histórica seleccionada queda en **71/71 pruebas verdes** y el bloque específico 0.33 en **8/8**. La suite total del repositorio no se declara ejecutada. Véase `docs/V033_TURKEY_GAZIANTEP_AND_NEXT_PROFILES.md`.

## Estado · checkpoint 0.32.0-historical-metadata-turkey-profiles

La 0.32 cierra el frente de **metadatos históricos de recinto y árbitros** para las cuatro ligas reconstruidas y profundiza de forma masiva la liga turca. Los 54 huecos de estadio detectados al comenzar 0.31 quedan reducidos a cero: los nombres de recinto se enlazan por temporada/partido y no se inventan aforos ni dimensiones modernas. Bélgica conserva un pool arbitral histórico completo de 25 nombres; Turquía queda cerrada con 34 árbitros cuyas apariciones suman los 240 partidos de liga; Rusia con 33 árbitros y 306 partidos; Grecia permanece deliberadamente como subconjunto histórico documentado de 11/45.

En Turquía se han curado **162 perfiles** en seis bloques de plantilla (Fenerbahçe, Samsunspor, Trabzonspor, Bursaspor, Gençlerbirliği y Kocaelispor), con **96 correcciones de posición funcional**. Se han recuperado cinco futbolistas de plantilla inicial que no aparecían en el staging basado en uso liguero: Vedat Emmez, Serkan Gültang, Sunay Kahraman, İsmail Ünal y Fevzi Açıkgöz. Turquía pasa de 414 a **419 jugadores activos**; el total de Bélgica+Turquía+Rusia+Grecia queda en **1.813**. No se aplica ninguna regla 75/25: las altas nuevas materializan atributos fijos a partir de comparables originales 1993-94 de la misma línea/valoración y conservan sus IDs de comparables para auditoría.

Las **1.813 biografías** de los jugadores activos se regeneran después de cada corrección de perfil para impedir texto obsoleto. Hay **36 retratos BDFutbol realmente empaquetados** y normalizados a 40×55 JPEG; los estados de registro/cola distinguen foto pendiente de foto físicamente incluida. Los casos ambiguos conservan `profile_review_required` en vez de recibir una especialización inventada. La discrepancia de fecha de nacimiento de Ace Khuse y el conflicto posicional de Fevzi Açıkgöz están documentados explícitamente.

La regresión dirigida de cierre 0.23→0.32 queda en **84/84 pruebas**. No se presenta como ejecución de toda la suite del repositorio. Véase `docs/V032_HISTORICAL_METADATA_CLOSURE_AND_TURKEY_PROFILES.md`.

## Estado · checkpoint 0.24.0-bel-tur-rus-1993-data

**P1–P10 siguen cerrados; 0.24 continúa la expansión internacional con prioridad absoluta a identidad y realismo.** No se introduce una fórmula nueva de valoración: los jugadores creados se materializan como datos fijos comparándolos con futbolistas originales 1993-94 de la misma posición/nivel, con perfiles específicos para los nombres relevantes. Los 10.528 jugadores originales permanecen intactos.

La auditoría acumulada cubre ahora **428 altas históricas externas**. Todas se comparan contra los 10.528 jugadores originales y las nuevas incorporaciones de esta pasada se contrastan además contra los **37.312 registros del MDB completo**. El resultado actual mantiene cero colisiones fuertes/ambiguas y cero duplicados exactos generados. El caso de control Dmitri Popov continúa resuelto como el único ID original 515 del Racing.

La profundidad de selección se amplía específicamente en **Bélgica, Turquía y Rusia**: los pools con nacionalidad internacional explícita quedan en 41, 49 y 42 futbolistas respectivamente. La tanda 0.24 crea 61 jugadores reales (15 belgas, 40 turcos y 6 rusos), todos con club/posición histórica documentados, revisión de perfil cerrada y registro permanente para el flujo de fotos BDFutbol. El objetivo de producto ya no es sólo tener 22 convocables, sino aproximarse a 40 opciones reales por selección para absorber lesiones y sanciones.

La reconstrucción de las ligas belga, turca y rusa 1993-94 queda iniciada de forma segura en `data/football9394/bel_tur_rus_1993_94_league_foundations.json`: **52 clubes históricos** con sus páginas de plantilla BDFutbol y reglamentos de época. No se activan todavía como ligas jugables porque las filas 52/57/15 del MDB suministrado pertenecen a la edición 2017; reutilizarlas mezclaría plantillas modernas. Esos IDs están deliberadamente bloqueados y cada futura liga histórica tendrá un ID runtime propio. La activación exige un mínimo de 18 jugadores 1993-94 reales por club.

El registro de altas y la cola de fotos conservan ahora también `historical_club_1994` y `historical_position_1993_94`, además de ID, nombre, nacimiento, país, lote/fuente, control de duplicados y campos BDFutbol. Véase `docs/V024_BEL_TUR_RUS_1993_DATA.md`.

**P1–P10 permanecen cerrados.** El plan ambicioso de carrera completado en 0.20 se conserva como base: P6 firma estadística individual; P7 mercado de planificación; P8 reglamento 1993-94 congelado; P9 carrera internacional; P10 gates de carrera. Véase `docs/V020_P6_P10_PLAN_CLOSED.md`.

La economía de carrera usa ahora una escala de pesetas 1993-94 mucho más expresiva: el valor de mercado crece con fuerza en la élite (un 89 se calibra alrededor de 450 M ptas.), las fichas inferidas comparten esa escala y la IA/mercado se han reequilibrado para que clubes modestos sigan encontrando objetivos realistas. Los importes siguen siendo estimaciones de gameplay cuando la fuente no contiene un dato histórico contractual concreto.


La **edad congelada es ahora la política predeterminada** de carrera: el reparto histórico de 1993-94 no envejece cronológicamente, no se retira por edad y no es sustituido por cantera/newgens. Esto es una concesión deliberada al realismo para preservar el apego al reparto original. La profundidad longitudinal permanece: rendimiento, minutos, entrenador, lesiones, forma, adaptación, tutela y experiencia pueden mejorar o deteriorar atributos concretos. La carrera cronológica sigue disponible como alternativa explícita.

P4 quedó cerrado con una vertical profunda: capitán y líderes, competencia por puestos, tutela entre futbolistas del reparto inicial, reacción colectiva a lesiones/ventas importantes, reencuentros y **promesas explícitas de rol** evaluadas por las titularidades reales de los siguientes ocho partidos. Cumplir o romper una promesa cambia relación y satisfacción, nunca la capacidad neutral del jugador. Véase `docs/V015_FROZEN_CAST_DRESSING_ROOM.md`.

La 0.11 amplía la carrera viva: una destitución ya no termina la partida. El mánager conserva reputación, récords e historial, recibe proyectos y puede encadenar etapas en distintos clubes de la misma liga. La 0.10 mantiene además la **carrera viva con memoria**: rivalidades persistentes, relación mánager–jugador con consecuencias contractuales, historias emergentes que se abren y resuelven por hechos reales, mercado de entrenadores IA y récords/archivo de la etapa. D1–D9 y F1–F8 permanecen cerrados. Véase `docs/V010_LIVING_CAREER.md`.

El repo contiene únicamente el dominio de fútbol Míster 93/94, su frontend, tests, snapshot normalizado y los gráficos históricos utilizados por las entidades del mundo activo.

El motor mantiene **M0–M15 como base funcional**, el rediseño moderno **R1–R10 cerrado** y la profundización futbolística **F1–F8 cerrada en esta pasada**. Jugadores, entrenadores, táctica, partido, plantilla, mercado y carrera larga consumen ya la información recuperada de la MDB en lugar de reconstruirla artificialmente.


### D1–D9 · profundidad visible, bucle futbolístico y gate 1080p

La ficha de jugador y la ficha de club siguen siendo las superficies de referencia, pero el nuevo lenguaje ya se ha propagado al bucle diario. Inicio se organiza como una jornada —próximo rival, posición, forma, decisiones, figuras, tensiones y noticias—; Plantilla y Tácticas muestran encaje del XI y conflictos con el plan; Mercado explica por qué un objetivo puede encajar; y el directo incorpora previa con entrenador/plan rival, tres amenazas, árbitro y estadio, además de una lectura causal al terminar.

El entrenador fuente del club controlado sigue apareciendo sólo como **entrenador al inicio / referencia histórica**: el plan actual es el del jugador. El contrato D1–D8 queda automatizado en `frontend/tools/ui-quality.mjs`. Detalle en `docs/D1_D8_FOOTBALL_FIRST_PRODUCT.md`.

**D9 queda cerrado como gate de composición Chromium 1920×1080**: Inicio, Plantilla, jugador, club, Táctica, Mercado, Competiciones, previa, directo y postpartido se han renderizado con los templates/CSS reales y datos 93/94 representativos. La pasada corrigió tamaño tipográfico real, visibilidad de Guardar táctica, espacio muerto de previa, controles del banquillo y postpartido. `vite build` sigue siendo un gate técnico separado no certificado porque el binario Vite no está disponible en este entorno.

La revisión visual cubre shell, Inicio, Plantilla, ficha, Tácticas, directo, Mercado, Competiciones, Economía, Noticias, Selecciones, Club, Historia, Calendario y Nueva carrera. La auditoría de fuente está en `docs/MDB_DEEP_SOURCE_AUDIT.md` y el cierre F1–F8 en `docs/F1_F8_FOOTBALL_DEPTH_CLOSED.md`.

La base de juego heredada mantiene:

- consejo, objetivos, confianza explicable y riesgo de destitución con inercia;
- noticias causales y hemeroteca persistente;
- navegador universal de competiciones, reglas, resultados, calendarios y palmarés;
- cierre de temporada, archivo histórico, verano y pretemporada real;
- ritmo contextual: pulsos cortos en pretemporada y avance hacia partido/incidencia durante la temporada;
- puestos especializados y compatibilidad posicional en once, mercado e IA;
- reglas de extranjeros por competición para usuario e IA;
- 18 jugadores como suelo de plantilla, objetivos dinámicos de profundidad de 20–24 y XI legal como gate separado;
- IA que protege puestos estructurales, repara plantillas y no vende al único portero;
- jerarquía de clubes dinámica y gradual, sin convertir una gran temporada en un salto instantáneo de categoría;
- economía longitudinal recalibrada para conservar diferencias de tamaño sin crecimiento explosivo;
- gate longitudinal de 10 temporadas con controles deportivos, económicos y de plantilla, certificado en la pasada M15; en 0.9 la recertificación completa excede la ventana y se complementa con el gate F6 focal de diez años + rollovers 1994-95/1995-96.
- La certificación histórica de **174 tests de fútbol** de M15 se conserva como referencia; el cierre 0.9 añade sus propios gates dirigidos y no presenta el longitudinal completo como re-certificado.


**Profundización F1–F8 cerrada en 0.9.0-f1-f8-depth-closed**: identidad de jugador, entrenadores fuente, trece formaciones, causalidad de partido, jerarquías/tensión, lesiones específicas persistentes, mercado por necesidad/encaje, edad dinámica, retiradas, cantera/newgens fuente y gate de realismo quedan conectados al runtime. El gate de 120 partidos queda en 2,575 goles/partido frente al objetivo 2,603 de Primera 1993-94.

**Auditoría profunda de fuente cerrada en 0.8.0-source-recovery**: la MDB ya no se trata como un simple origen de jugadores/clubes. Se recuperan entrenadores, tácticas, árbitros, roles, patrones, lesiones, estadios, ciudades/regiones/clima, países, nombres ponderados e infraestructura de prensa, con niveles explícitos de confianza temporal. Entrenadores y árbitros ya afectan al runtime; la polivalencia y rasgos fuente llegan a la ficha/motor de selección; y `OrigenVasco` gobierna la política de fichajes del Athletic.

**Rediseño de producto R1–R10 cerrado en 0.7.0-r10**: shell, Inicio, Plantilla, ficha, Táctica, directo, Mercado, Competiciones, Economía, Noticias, Selecciones, Club, Historia, Calendario y Nueva carrera comparten la misma gramática moderna.

El plan completo está en `docs/MASTER_GAME_PLAN.md`. Los cierres y la revisión activa están documentados en:

- `docs/BLOCK_01_FOUNDATION_GAMEPLAY.md`
- `docs/BLOCK_02_TACTICS_MATCH_MARKET_ECONOMY.md`
- `docs/BLOCK_03_M9_M15_COMPLETE_MANAGER.md`
- `docs/R1_MODERN_PRODUCT_REDESIGN.md`
- `docs/R2_R6_MODERN_CORE_WORKSPACES.md`
- `docs/R7_R10_PRODUCT_REDESIGN_CLOSED.md`
- `docs/F1_F8_FOOTBALL_DEPTH_CLOSED.md`
- `docs/MDB_DEEP_SOURCE_AUDIT.md`
- `docs/D1_D3_REFERENCE_SURFACES.md`
- `docs/D1_D8_FOOTBALL_FIRST_PRODUCT.md`
- `docs/D9_CHROMIUM_VISUAL_GATE.md`
- `docs/V1_AMBITIOUS_CAREER_PLAN.md`
- `docs/V015_FROZEN_CAST_DRESSING_ROOM.md`
- `docs/V020_P6_P10_PLAN_CLOSED.md`
- `docs/V021_STUDIO_USA94_NATIONAL_TEAMS.md`

## Ejecutar backend

```bash
python run_football9394.py
```

## Frontend

```bash
cd frontend
npm ci
npm run dev
```

La build de producción requiere que las dependencias npm estén disponibles. El chequeo estructural SFC puede ejecutarse sin iniciar la aplicación:

```bash
npm run check:sfc
npm run check:ui
npm run check:vue
```

## Datos

El runtime consume `data/football9394/historical_snapshot.json`. La MDB fuente completa se utiliza para trazabilidad/verificación y no se duplica en el repo limpio. Los clubes fuera del selector de carrera pueden seguir existiendo en el universo cuando una competición o la historia los necesita.

Los contratos/salarios de jugador que la MDB no proporciona de forma utilizable se marcan como datos inferidos por la carrera; no se presentan como hechos históricos. La MDB sí contiene contratos/sueldos de entrenador, pero pertenecen a una fuente de edición temporalmente mixta y requieren curación antes de etiquetarlos como 1993-94.
