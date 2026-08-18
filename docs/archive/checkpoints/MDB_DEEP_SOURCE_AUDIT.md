# Auditoría profunda de `basedatos.mdb` · recuperación de fuente

Estado: **auditoría física completa + primera integración runtime**.

Esta pasada existe porque el importador histórico anterior trataba la MDB casi sólo como fuente de `Liga`, `Torneo`, `Equipo`, `Jugador` y calendarios. Eso estaba descartando una parte importante del diseño original y, peor, algunas tablas seguían físicamente en el archivo aunque hubieran perdido su entrada normal en el catálogo de Access.

## 1. Qué se ha inspeccionado

Se ha recorrido el archivo Jet4 completo: **46 tablas visibles, 132 consultas, 35 relaciones, 17 formularios** y todas las páginas TDEF físicamente recuperables. El barrido de TDEF huérfanas detectó como entidades de juego útiles que habían desaparecido del catálogo normal:

- `Entrenador`: **3.199 filas · 33 campos**.
- `Pais`: **222 filas · 23 campos**.
- `Tactica`: **123 filas · 13 campos**.
- `MedioComunicacion`: **262 filas · 11 campos**.

No se han encontrado otras tablas de juego huérfanas comparables tras el barrido físico. El lector Jet4 se amplió además para resolver los valores `MEMO` de Access; gracias a ello se recuperan las descripciones de patrones y otros textos que antes aparecían como punteros binarios.

## 2. Inventario recuperado que sí puede alimentar el juego

El catálogo derivado `historical_source_catalog.json` conserva:

- **3.199 entrenadores**.
- **123 tácticas** con geometría de 11 jugadores, roles, ámbitos, libertades, presión y marcaje.
- **3.511 árbitros**.
- **2.094 estadios**.
- **5.402 ciudades**, **312 regiones**, **7 climas**, **222 países** y **6 continentes**.
- **18 roles especializados** de futbolista.
- **24 patrones/arquetipos de jugador** con descripción original.
- **33 lesiones genéricas**, **154 lesiones específicas**, **23 zonas corporales genéricas** y **48 específicas**.
- **80.997 nombres/apellidos ponderados por país**, más grupos de idioma y país–idioma.
- **262 medios** y **52 corresponsales**, conservados sólo como estructura porque sus nombres pertenecen mayoritariamente a una edición moderna.

El runtime carga este catálogo de forma perezosa: no se añaden ~9,5 MB al coste de arranque normal si un subsistema no necesita esos datos.

## 3. Entrenadores: entidad de primera clase, no ID decorativo

`Equipo.Entrenador` tiene relación física con la tabla huérfana `Entrenador`. Entre los **410 clubes domésticos** del corte 1993-94 hay **404 IDs de entrenador distintos y 404/404 resuelven**. Contando los 441 clubes cargados por competiciones continentales hay 433 IDs y también resuelven todos.

La fuente define para cada técnico:

- calidad de entrenador (`CALIDAD`);
- reputación/categoría;
- táctica principal y variantes ofensiva/defensiva;
- tendencia defensiva / normal / ofensiva;
- frecuencia de rotaciones;
- uso de cantera;
- disciplina;
- relación con jugadores;
- ojo para futbolistas;
- uso de jugadas de estrategia;
- preferencia por plantilla corta;
- hasta cinco patrones de futbolista preferidos;
- contrato, años cumplidos y salario de la edición fuente.

Los formularios de la propia MDB documentan que `CALIDAD` representa la precisión con la que los jugadores siguen sus órdenes y su capacidad para lograr objetivos, y que `TendenciaJuego`, combinada con calidad, interviene en el desarrollo de futbolistas.

### Integración hecha

Los clubes IA ya construyen su plan de partido desde el entrenador fuente. La calidad **no añade una bonificación plana a la media del equipo**. El entrenador modifica decisiones: sistema, mentalidad, presión, rotación y desarrollo individual. El desarrollo depende de calidad + encaje con el futbolista + edad/etapa + uso de cantera + relación + patrones preferidos. El equipo controlado por el usuario no conserva artificialmente el estilo del técnico histórico: al tomar el puesto, el entrenador eres tú.

### Cautela temporal

La MDB mezcla ediciones. Cruyff–Barcelona y Toshack–Real Sociedad son ejemplos coherentes, pero otros emparejamientos son posteriores. Por eso `manager_id` y perfiles se preservan como fuente, pero la etiqueta “histórico 1993-94 confirmado” exige curación temporal por club.

## 4. Futbolistas: profundidad que estábamos perdiendo

Además de los atributos ya importados, `Jugador` guarda **18 valoraciones de rol (`Rol1…Rol18`)**. No son posiciones inventadas: permiten conocer polivalencia y aptitud secundaria real de la fuente. En el corte completo de 10.528 jugadores, **10.187 tienen alguna valoración explícita de rol**.

Los 18 roles son: portero; lateral derecho/izquierdo; centrales derecho/izquierdo; líbero; organizador defensivo; organizador; mediapunta central; centrocampista/interior/mediapunta/extremo por ambas bandas; delantero.

También se recuperan siete rasgos ocultos documentados por el editor original:

- individualista;
- busca el último pase;
- conserva el balón;
- tiro de media/larga distancia;
- tiende hacia dentro desde banda;
- juega de primeras;
- piscinero.

Se conservan también regularidad, visión, trabajo/lucha, agresividad, anticipación, liderazgo, desmarque, potencia de tiro, balón parado, pie dominante, altura/peso, dorsal favorito, propensión a lesiones, progresión media, afecto de la afición, club de cantera, club anterior, años allí y opción de recompra.

`ProgresionMedia` sí aporta señal y el editor la documenta como escala 0–9. En cambio `Progresion` vale 1 en todos los jugadores activos revisados y se descarta como campo sin información.

### Athletic Club

`Jugador.OrigenVasco` es un flag explícito. Los **22/22 futbolistas del Athletic Club 1993-94** están marcados. El snapshot ya lo preserva y el mercado impide al Athletic incorporar a un jugador sin ese flag. Esto evita inferencias frágiles por apellido, nacionalidad o lugar de nacimiento. En el corte completo hay 497 futbolistas marcados de origen vasco.

## 5. Árbitros: sí, son utilizables, con una advertencia crítica

Las **23 ligas** del corte 1993-94 tienen pool arbitral en la fuente. Se conservan liga/colegio, calidad y tendencias de amarillas/rojas.

La tabla `Arbitro2` ha sido decisiva para auditar la fiabilidad: coincide con `Arbitro` en IDs y parámetros futbolísticos, pero **1.064 fechas de nacimiento difieren**. Además existe una consulta llamada `Actualizar fechas de nacimiento 1993 Arbitro`. Conclusión: la fecha de nacimiento no debe presentarse como dato histórico fiable y el nombre exacto necesita curación temporal por liga.

### Integración hecha

Los partidos de liga eligen árbitro de forma determinista desde el pool de su competición. Su tendencia modifica la probabilidad de amarilla/roja; su calidad no altera mágicamente el resultado. El árbitro queda persistido en el resultado y también participa en el **directo del usuario**. Un gate estadístico comprueba que, con los mismos jugadores y semillas, un árbitro severo genera más tarjetas que uno permisivo.

## 6. Lesiones y área médica

La MDB ya contiene un modelo médico mucho más rico que el actual:

- tipo genérico de lesión y posibles derivaciones;
- lesión específica;
- zona corporal y lateralidad;
- tiempo mínimo/máximo de recuperación conservadora;
- tiempo mínimo/máximo con operación;
- frecuencia;
- posibilidad de operación;
- molestias si no se opera;
- infiltrabilidad;
- mapa corporal con coordenadas para derecha/izquierda.

Además `Jugador.Lesiones` está documentado: 0 normal, 1 propenso, 2 muy propenso, 3 crónico.

Los campos `LesionActual*` existen pero están a cero en los 9.928 jugadores domésticos activos del corte: no sirven para inventar un parte médico inicial. El **catálogo de lesiones y la propensión sí sirven** para F3/F4 y deben sustituir progresivamente el genérico “Problemas físicos”.

## 7. Estadios, ciudades, clima y geografía

Los **410 clubes domésticos tienen estadio resoluble**. El estadio aporta nombre, ancho, largo, aforo, estrellas, calidad del césped y ciudad. La ciudad enlaza con país, clima y hasta dos regiones opcionales, además de gentilicios.

Esto permite, sin inventar estructura:

- previa y ficha de club más ricas;
- dimensiones reales del terreno como input táctico;
- clima y césped como contexto de partido;
- generación regional de cantera;
- políticas de club/región;
- gentilicios correctos en noticias.

Nombres y capacidades concretas pueden proceder de ediciones posteriores: se mantienen con confianza temporal mixta hasta curación.

`CalendarioTorneoFinal` también estaba ignorado. Para tres torneos activos hay estadios fuente asociados a la final; se conservan como `final_venue_hints` para que el ruleset pueda contrastarlos con la regla histórica verificada.

## 8. Cantera y construcción de plantilla

`Equipo` contiene una pequeña filosofía deportiva que hasta ahora casi no usábamos:

- `Nivel_cantera`: básica / nivel primer equipo / prolífica;
- `Estilo_cantera`: sólo región / región / país / internacional / muy internacional;
- `Canterano_especial`: patrón de futbolista producido con mayor frecuencia;
- `Confeccion_plantilla`: fichajes primero / cantera primero / mezcla;
- `Secretario_tecnico_estrella`: especialista excepcional para detectar jóvenes desconocidos;
- filial y escalón de filial;
- ciudad deportiva y residencia juvenil.

Esto es materia prima directa para F5/F6: las academias no tienen por qué producir los mismos newgens ni los clubes IA construir plantillas de la misma forma.

## 9. Generación de jugadores: fuente excelente para carrera larga

`_NombresYApellidos` contiene **80.997 registros ponderados por país**, separados entre nombres y apellidos. La base incluye grupos lingüísticos, relación país–idioma, 312 regiones y el campo de país que indica uso de segundo apellido.

Por tanto los futuros newgens pueden generarse con:

- nombres plausibles del país;
- ponderación real de frecuencia de la fuente;
- segundo apellido cuando corresponde;
- origen regional;
- idiomas plausibles;
- estilo de cantera del club;
- patrón de jugador preferido de esa cantera.

No necesitamos listas modernas externas para el núcleo de nombres.

## 10. Club, identidad e historia

`Equipo` aporta además presidente, socios, presupuesto, deuda, rival principal y regional, palmarés nacional/continental, sanción inicial de puntos, sanción FIFA, gentilicios y gentilicio de colores. No existe una tabla rica de presidentes/directores comparable a `Entrenador`: el presidente es texto y el director deportivo es principalmente un indicador de nivel. Esos datos se pueden usar, pero no debemos fingir una entidad personal que la fuente no contiene.

## 11. Competiciones: usar como auditor, no como autoridad automática

`Liga` tiene 55 campos y `Torneo` 66. Además de extranjeros y calendarios contienen días permitidos, parón navideño, ciclo de amarillas, posiciones/plazas, fases, invitados, periodicidad, final de consolación, anfitrión, campeón anterior, audiencia, reglas de ida/vuelta y otras señales.

La MDB mezcla épocas, así que estos campos **no sustituyen** los rulesets históricos verificados que ya tiene el juego. Sí deben alimentar un auditor: si el ruleset y la fuente discrepan, el gate obliga a documentar por qué.

## 12. Medios, corresponsales y televisión

La estructura es útil para una futura prensa con personalidad: medio, tipo, país/región/ciudad, club asociado, prestigio, seguimiento, fanatismo y corresponsales. Pero nombres como medios/corresponsales concretos y la tabla `TV` son claramente de ediciones modernas (incluyen TDT y actores contemporáneos). Política:

**usar esquema y relaciones; no presentar esos registros como prensa de 1993 hasta curarlos/reemplazarlos por un dataset histórico.**

## 13. Datos que NO vamos a inflar artificialmente

- `ContratoJugadorEquipo`: **0 filas**.
- `Progresion`: sin señal en jugadores activos.
- `LesionActual*`: sin lesiones iniciales en el corte activo.
- `FIFA/FIFA2/PuntosFIFA`: muy parcial/editorial; no sustituye nuestras valoraciones.
- `Media_*_forzada`, `Completar*`, `LoadTmp`, revisiones de escudo: herramientas del editor.
- `Datos`, `Opciones`, `Usuario`, `UsuarioCambio`, `Errores de pegado`, `Jugador_ErroresDeExportación`, `FB_SORT`: mantenimiento/infraestructura, no mecánicas de juego.
- `TacticaUsuario` contiene explícitamente una táctica “Guardiola” fechada en 2012: prueba adicional de mezcla temporal.

## 14. Mapa directo a F1–F8

### F1 · Identidad del futbolista
Roles 1–18, polivalencia, siete rasgos ocultos, pie, regularidad, visión, trabajo, agresividad, anticipación, liderazgo, desmarque, progresión media, lesión y afecto.

### F2 · Táctica y entrenadores
Entrenadores completos + 123 tácticas + patrones preferidos + rotación + cantera + disciplina + relación + variantes de partido.

### F3 · Motor de partido
Árbitros, dimensiones/césped/clima, rasgos de jugador, lesiones específicas, uso de estrategia y geometría táctica.

### F4 · Plantilla y tensión
Relación/disciplinas del técnico, afecto afición, dorsal favorito, club anterior, cantera, lesión/operación/molestias y rotación.

### F5 · Mercado inteligente
Filosofía de construcción de plantilla, ojo del entrenador, especialista de captación, cantera, presupuesto/deuda, opción de recompra, reglas de extranjeros y política Athletic.

### F6 · Carrera larga
80.997 nombres ponderados, regiones/idiomas, segundo apellido, academias distintas, patrones, progresión media, lesión, entrenadores como actores persistentes.

### F7 · Belleza y facilidad de uso
Estadio/ciudad/región/gentilicios, mapa corporal médico, identidad de club y prensa estructurada sin falsear la época.

### F8 · Gate de realismo
Consultas de mantenimiento originales como QA semántico, redundancias `Arbitro/Arbitro2`, cobertura entrenador–club, árbitro–liga, estadio–club y diferencias documentadas entre source hints y rulesets.

## 15. Gates ya añadidos

`backend/tools/audit_football9394_source_catalog.py` debe ejecutarse contra los JSON derivados y comprueba, entre otros:

- 410 clubes domésticos;
- 404 IDs de entrenador domésticos y 0 sin resolver;
- 433 IDs entre todos los clubes cargados y 0 sin resolver;
- 23 ligas y 0 sin pool arbitral;
- 0 clubes domésticos sin estadio;
- 22/22 jugadores iniciales del Athletic con `OrigenVasco`;
- exactamente 1.064 conflictos de fecha entre `Arbitro` y `Arbitro2`.

La MDB original no se incluye en el checkpoint. El proceso reproducible es:

`python backend/tools/build_football9394_source_data.py <ruta-a-basedatos.mdb>`

seguido de:

`python backend/tools/audit_football9394_source_catalog.py`

Esta auditoría pasa a ser el inventario canónico: antes de inventar un dato o sistema para F1–F8, hay que comprobar primero si la fuente ya lo contiene.
