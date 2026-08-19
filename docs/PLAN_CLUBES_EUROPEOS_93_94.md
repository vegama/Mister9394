# Plantillas reales para los clubes europeos de 1993-94

Documento de traspaso. Recoge lo averiguado, lo que ya está construido y lo que
queda por hacer, con las URLs y los formatos concretos para no repetir el
reconocimiento.

---

## 1. El problema que hay que arreglar

El juego tiene **24 clubes de ligas que no simula** —Lillestrøm, Valur,
Degerfors, Shelbourne, APOEL, Maccabi Haifa, Cardiff, Panathinaikos, Brøndby,
Odense, Legia, Ferencváros, Hajduk, Austria Viena, Shakhtar y compañía—. Están
ahí porque jugaron Europa esa temporada, y esa parte es correcta.

Lo que no es correcto son sus plantillas: **463 jugadores inventados**. Los
generó la base original de UNIFUTBOL para rellenar los clubes cuya liga no
modelaba. No es una sospecha, está comprobado de tres formas:

- Los futbolistas reales de esos clubes **no existen en toda la base**. Del
  Rosenborg del 93 no está By Rise, ni Skammelsrud, ni Sørloth. Del Steaua no
  está Lăcătuş, ni Stelea, ni Prodan. Sí está Dan Petrescu, en el Genoa, que es
  exactamente donde jugaba: la base tiene a los de verdad cuando la liga está
  modelada.
- En su lugar hay mezclas del generador: "Elbasan Bärkroth" en el Rosenborg,
  "Mushaga Lusa Risholt Joar Bahati Namugunga", un Steaua con "Alanzinho Douglas
  de Amorim".
- Muchos apellidos son de futbolistas reales pero de los 2000 y 2010 —Hradecký,
  Pjaca, Cibicki, Sapunaru— con fecha de nacimiento fabricada para encajar en el
  93. El Lillestrøm tiene a "Simen Søraunet Myhra", noruego real nacido en 1997,
  aquí puesto en 1968.

Además **faltan 61 clubes** que sí disputaron las tres competiciones europeas.

**Decisión tomada:** sustituir las plantillas inventadas por las reales y añadir
los clubes que faltan al pool europeo, sin liga propia, como los 24 actuales.
Los 463 generados **se borran** (decidido explícitamente, no se dejan retirados).

---

## 2. Fuentes verificadas

### Plantillas: BDFutbol

Es la fuente buena y además la que ya usa el proyecto. Da plantilla por club,
temporada y competición, **con foto de todos los jugadores**.

```
plantilla   https://www.bdfutbol.com/es/t/t1993-94<id_club>.html
cuadro      https://www.bdfutbol.com/es/t/t1993-94aCHA.html   (Copa de Europa)
            https://www.bdfutbol.com/es/t/t1993-94aREC.html   (Recopa)
            https://www.bdfutbol.com/es/t/t1993-94aUEF.html   (Copa de la UEFA)
buscar club https://www.bdfutbol.com/es/buscar.php?d=<nombre>&be=on
ficha       https://www.bdfutbol.com/es/j/j<id_jugador>.html
foto        https://www.bdfutbol.com/i/j/<id_jugador>.jpg
escudo      https://www.bdfutbol.com/i/eg/<id_club>.png
```

Ejemplo comprobado: el Rosenborg es `10038` y su página da 19 jugadores reales
—Rise, Bragstad, Kvarme, Ingebrigtsen, Skammelsrud, Leonhardsen, Riseth,
Strand— todos con retrato que responde 200.

**Aviso:** BDFutbol da la plantilla **de la eliminatoria europea**, no la de
liga. Un club que cayó en primera ronda puede dar 14 o 16 fichas. Es plantilla
real y verificable, pero no siempre completa.

### Lo que NO sirve

- **Wikipedia** no tiene páginas de temporada de estos clubes. Ni
  `1993 Rosenborg BK season`, ni la noruega, ni la de la liga. Sí sirve para la
  **lista de participantes**, que es de donde salen los 149.
- **El buscador de BDFutbol con `be=on`** encuentra clubes extranjeros, pero su
  índice `/e/e.html` es sólo de España.
- **worldfootball.net** responde 403.
- **Transfermarkt** sí funciona (Rosenborg es el `195`, `/kader/verein/195/saison_id/1993`)
  y queda como respaldo para lo que BDFutbol no cubra. Ojo: para ligas de año
  natural `saison_id/1993` titula "squad 1994".

### Escudos

Primero los gráficos originales del juego, y lo que falte de BDFutbol:

```
C:\UNIFUTBOL\UNIFUTBOL v14.5\datos.vin\1993\graficos\escudos\<id_equipo>.gif
```

2.170 escudos nombrados por id de equipo de la base, más 1.999 estadios, 227
banderas y unas 9.000 fotos de jugador en `graficos/jugadores/1..9/<id>.jpg`.

**`v14.5\datos.vin\1993\basedatos\basedatos.mdb` es la base que importó el
proyecto**: 2.281 equipos y 37.312 jugadores, que cuadra al dígito con
`source_counts` del snapshot. La copia de `UNIFUTBOL v11` es más antigua
(2.256 / 36.596) y no debe usarse.

---

## 3. Trampas del formato ya resueltas

Están resueltas dentro de las herramientas, pero conviene saberlas:

- **El identificador del escudo puede llevar sufijo de letra**: el Valur es
  `10657b`. Aceptar sólo dígitos se comía la mitad de los clubes (59 en vez de
  117).
- **La tabla del cuadro no es simétrica**: el escudo del local va *detrás* de su
  nombre y el del visitante *delante*. Con un solo patrón sale la mitad.
- **Las rondas se filtran en el navegador**, no en el servidor: la página ya
  trae todas.
- **Wikipedia mete a los máximos goleadores con el mismo icono de bandera** que
  los clubes. Hay que acotar la lectura a la sección de equipos clasificados o
  Stoichkov y Klinsmann entran en la lista como si fueran equipos.

---

## 4. Herramientas ya construidas

| Fichero | Qué hace |
|---|---|
| `backend/tools/european_1993_94_participants.py` | Lee de Wikipedia los 149 participantes de las tres competiciones y marca cuáles están ya en el juego. Salida: `data/football9394/european_1993_94_participants.json` |
| `backend/tools/bdfutbol_european_1993_94_clubs.py` | Saca de los cuadros de BDFutbol el mapa club → identificador. 117 clubes. Salida: `data/football9394/bdfutbol_european_1993_94_clubs.json` |

Ambas tienen tabla de alias a mano para los nombres que no casan.

---

## 5. Estado del emparejamiento

- **149** participantes europeos según Wikipedia.
- **61** no están en el juego.
- **42** de esos 61 casan solos con un identificador de BDFutbol.
- **19** existen en BDFutbol con otro nombre y necesitan alias escrito a mano:
  Aalborg=AaB, København=Copenhagen, HB=HB Tórshavn, Östers=Öster, y además KR,
  Vác, ÍA, Crusaders, Gloria Bistrița, Norrköping, Bohemians, Botev Plovdiv,
  Admira/Wacker, DAC Dunajská, HJK, Albpetrol Patos, Slavia Prague, Valletta,
  Slovan Bratislava.

**No emparejar por aproximación.** Se intentó y ataba Gloria Bistrița con el ÍA.
Los alias van escritos y revisables, como ya se hizo con Olympiakos Pireas,
Sporting Lisboa y Hearts.

---

## 6. Plan de trabajo

### Paso 0 — cerrar lo anterior
El pool de selecciones y las nacionalidades están terminados pero **sin
comprometer**. Comprometerlos primero, para no mezclar los dos trabajos.

### Paso 1 — piloto con el Rosenborg
De punta a punta y validarlo antes de repetir:

1. Plantilla de `t1993-9410038.html`, con identificador de BDFutbol por jugador.
2. **Reconciliar contra lo que ya existe**, empezando por `Otros-Noruega`, que
   tiene 10 fichas. Los internacionales de esos países ya están dentro y hay que
   reasignarlos, no volver a crearlos.
3. Crear sólo al que no esté.
4. Escudo del gráfico original `escudos/599.gif`.
5. Fotos por la tubería de retratos que ya existe.

### Paso 2 — los otros 60 clubes que faltan

### Paso 3 — sustituir las plantillas inventadas de los 24 actuales
Borrar los 463 generados y poner los reales.

### Contenedores "Otros-" con material aprovechable

27 suizos, 21 finlandeses, 18 rumanos, 17 daneses, 15 checos, 13 suecos,
12 croatas, 10 noruegos, 5 irlandeses, 2 húngaros, 1 norirlandés.

Falta contenedor para Islandia, Chipre, Israel, Gales, Polonia, Eslovenia,
Ucrania e Islas Feroe: se crean al vuelo.

---

## 7. Reglas que no se negocian

Son las que ya rigen el proyecto y han evitado varios destrozos:

- **Nunca crear a alguien que ya existe.** Reconciliar contra toda la base antes
  de dar de alta.
- **Ante la duda, no elegir.** Un homónimo irresoluble se aparta en un informe;
  nunca se adivina.
- **Nunca inventar futbolistas** para completar una plantilla corta.
- **No pisar trabajo de otras tandas.** El registro de creados y la cola de
  fotos son compartidos: conservar `bdfutbol_id`, `photo_status` y
  `duplicate_check` de quien los haya afinado.
- **Copia antes de tocar.** El universo está en git; `git checkout` lo devuelve
  intacto. Hay copias en `.backup_pool/`.

---

## 7 bis. Que esos jugadores tengan estadísticas temporada a temporada

Traer las plantillas reales resuelve quiénes son, pero deja un problema mayor:
esos clubes no tienen liga, así que no juegan, así que sus futbolistas **se
quedan congelados**. No suman partidos ni goles, no cambian de forma, no se
lesionan y no evolucionan. A la tercera temporada el Rosenborg sigue teniendo el
mismo once con los mismos números mientras el resto del mundo ha cambiado, y eso
se nota más que no tenerlo.

Afecta a más gente de la que parece: los 85 clubes europeos y, además, los más de
mil futbolistas del pool de selecciones que viven en contenedores `Otros-País`.

### Lo que no vale

**Simular sus ligas de verdad** es lo correcto y es inviable: tenemos uno o dos
clubes por país, no las ligas enteras. Meter el resto significaría inventarse
equipos, que es justo lo que este proyecto no hace.

**Dejar que se enfrenten entre ellos** en una competición inventada da
estadísticas causales de verdad, pero produce un calendario absurdo: el Rosenborg
jugando cada semana contra el APOEL y el Valur.

### Propuesta: temporada doméstica abstracta, en dos niveles

**Nivel 1, por defecto y barato.** Cada club sin liga juega una temporada
doméstica *abstracta*: un número de jornadas propio de su país y un rival
anónimo cuyo nivel sale del baremo de la competición. No se simulan partidos: se
reparten minutos, goles, asistencias, tarjetas y lesiones entre su plantilla real
según demarcación, calidad y jerarquía, con semilla determinista. Es lo bastante
bueno para que la ficha del jugador tenga historial y para alimentar el sistema
de progresión que ya existe, que es el verdadero premio: dejan de estar
congelados y empiezan a subir o bajar por rendimiento, que es exactamente lo que
se pidió para el mundo sin edad.

**Nivel 2, sólo donde se ve.** Cuando la carrera del usuario se cruza de verdad
con uno de estos clubes —le toca en Europa—, ese club sí se simula con el motor
de partido real durante esa temporada. Así el rival al que te enfrentas llega
con forma, lesiones y goleador de verdad. Se paga el coste sólo donde es
observable.

Sin esta separación el coste se dispara: 85 clubes por unas 30 jornadas son
2.500 partidos extra por temporada, y el avance de temporada ya es lo más lento
del juego.

### Cómo se hace realista de forma comprobable

Ésta es la parte importante y la que evita que sea a ojo. **Tenemos 21 ligas
simuladas de verdad como patrón de calibración.** Cualquier línea estadística
generada tiene que caer dentro de la distribución que producen esas ligas:

- goles del máximo goleador de un club, y del pichichi de su liga abstracta;
- reparto de minutos entre titulares, rotación y suplentes;
- porteros con portería a cero, tarjetas, días de baja por lesión;
- cuántos futbolistas de una plantilla pasan de N partidos.

Eso se puede escribir como prueba: se comparan los percentiles de lo generado
contra los de las ligas reales del juego y se exige que estén dentro de rango. Si
un delantero abstracto mete 60 goles, la prueba se pone roja. Es la diferencia
entre "parece razonable" y "está calibrado contra el propio juego".

### Los del contenedor `Otros-`: decidido, van a su club real

**Decisión tomada:** se les da de alta su club de verdad aunque ese club acabe
teniendo un solo futbolista. Casi todos traen ya el dato en
`historical_club_1994`, y en la base hay **584 clubes distintos entre ellos, 525
sin modelar**. Es preferible un Kaizer Chiefs con tres fichas a un
`Otros-Sudáfrica` con treinta: el jugador tiene club, el fichaje tiene origen y
la ficha dice la verdad.

Esto obliga a separar dos papeles que hasta ahora iban juntos:

**Club como empleador** —basta con un futbolista—. Da contrato, dorsal, origen
en el mercado y, sobre todo, el nivel de competición del que cuelga la temporada
abstracta. Los otros veinte de su plantilla simplemente no están modelados,
igual que no lo está el resto del mundo.

**Club como competidor** —necesita plantilla suficiente—. Sólo estos aparecen en
calendarios, sorteos y eliminatorias. Un club de cinco fichas nunca sale
emparejado, porque no podría alinear once. El precedente ya existe: es el mismo
criterio que `_functional_pool` aplica a las selecciones.

Sin esa separación, el primer sorteo europeo que le toque a un club de cinco
revienta.

Lo que hay que vigilar:

- Podrían aparecer hasta 525 clubes nuevos. Hay que marcarlos para que no
  ensucien los listados ni el buscador, y decidir si se ven o no.
- Muchos no tendrán escudo ni en los gráficos originales ni en BDFutbol.
- Los contenedores `Otros-País` no desaparecen: siguen siendo el sitio de quien
  no tiene club conocido.

### Abierto: que esos clubes compren y vendan

Idea sin cerrar, **pendiente de pensar mejor**. Si un club es empleador de
verdad, lo natural es que actúe en el mercado y no sólo sufra que le fichen. Un
Rosenborg que vende a su goleador y ficha un sustituto es más creíble que uno que
sólo pierde gente.

Lo que hay que resolver antes de tocar nada:

- **De dónde sale su dinero.** No tienen liga y por tanto no tienen ingresos
  modelados. Habría que darles presupuesto por nivel de competición y país, o que
  vivan sólo de lo que ingresan vendiendo.
- **Qué pasa si se vacían.** Un club de tres fichas que vende dos se queda en
  una, y si vende la última desaparece de facto. ¿Suelo mínimo, o se acepta?
- **Qué pasa si crecen.** Fichando podrían cruzar el umbral y pasar de empleador
  a competidor, y entonces el mundo cambia de forma con las temporadas. Puede ser
  una virtud —clubes que emergen— pero hay que quererlo a propósito.
- **Plausibilidad.** Un club noruego no debería fichar a una estrella brasileña.
  Aquí ya hay piezas: `foreign_rules.py` para el cupo de extranjeros y
  `market_ecosystem.py` para el comportamiento del mercado.
- **El riesgo de fondo:** que la IA de mercado los desangre y en cinco
  temporadas todos sus futbolistas reales acaben en las ligas modeladas. Es lo
  que pasa en la realidad, pero vaciaría de contenido justo lo que acabamos de
  construir.

  **El cupo de extranjeros ya frena bastante esto**, y conviene saber por qué:
  no limita sólo la alineación, limita el fichaje. `manager_career.py:3514`
  bloquea la operación con *"límite de extranjeros de plantilla alcanzado"*
  usando `ExPlantilla` del MDB, y `Ex11` cubre el once. Además aquí muerde más
  que en la realidad: como sólo hay 21 ligas modeladas, casi cualquier comprador
  de un jugador del Rosenborg es extranjero para él —el club noruego que en la
  vida real se lo habría llevado sin gastar cupo aquí no existe—.

  Tres grietas que dejan pasar agua igualmente:

  1. El grupo británico-irlandés cuenta como doméstico entre sí
     (`BRITISH_IRISH_DOMESTIC_GROUP`: Inglaterra, Escocia, Irlanda del Norte,
     Gales e Irlanda). Para el Shelbourne, el Bangor o el Crusaders eso no es un
     freno sino una autopista.
  2. El cupo es por club, no global. Veinte clubes con tres huecos cada uno
     siguen siendo sesenta fichajes por temporada.
  3. **Bosman queda fuera. Decidido.** En diciembre de 1995 los comunitarios
     dejaron de contar como extranjeros y el dique se rompió justo para los
     países europeos pequeños. Aquí **no se aplica**: el cupo de extranjeros no
     se relaja nunca, corra la carrera los años que corra. El objetivo declarado
     es que el talento siga lo más repartido posible, y ese cupo es la única
     pieza estructural que lo garantiza — sin él, cinco temporadas bastan para
     que los mejores de cada país pequeño acaben en cuatro clubes grandes.

     Es una desviación deliberada de la historia y hay que **etiquetarla como
     tal**, igual que se etiqueta todo lo generado frente a lo histórico. No es
     un olvido: es una regla de este mundo.

     Si con el tiempo se ve que el talento se concentra igual, los sitios por
     donde se escapa son los dos puntos de arriba —el pasillo británico-irlandés
     y que el cupo sea por club y no global—, no éste.
- **La oportunidad:** son una fuente estupenda de fichajes creíbles para el
  usuario, y encajan con `scouting.py` —descubrir a un chaval del Rosenborg antes
  que nadie—.

### La premisa: mundo sin edad, con los futbolistas de los 90 para siempre

Lo que se quiere jugar es la generación de mediados y finales de los noventa
**sin que nadie se retire**. La edad queda congelada; lo que cambia es el nivel,
por rendimiento, lesiones y minutos. Esto no es un capricho suelto: es lo que
justifica traer plantillas reales en vez de generarlas, y condiciona todo el
diseño de la progresión.

**El problema de quitar la edad** es que en un manager la edad es el motor de
todo: hace crecer al joven, declinar al veterano y retirarse al viejo, y así deja
sitio al siguiente. Si se quita y no se pone nada, todo el mundo converge hacia
arriba, nadie libera su puesto y a las cinco temporadas la liga es un museo de
ancianos intocables. Encima choca de frente con querer el talento repartido: si
Zubizarreta sigue siendo Zubizarreta para siempre, el portero joven no juega
nunca.

**Lo que sustituye a la edad:**

1. **El nivel se mueve en los dos sentidos.** Nadie se retira, pero quien juega
   mal, se lesiona o no tiene minutos **baja**. Es lo que mantiene la rotación
   sin necesidad de que nadie desaparezca.
2. **Cada futbolista tiene techo propio, y es el que tuvo de verdad.** Anelka
   puede llegar a ser el Anelka de 1999, no más. Skammelsrud llega hasta donde
   llegó. Así la generación de los noventa emerge sola con las temporadas sin
   que nadie se invente una estrella.
3. **Los jóvenes suben más rápido.** Ya está la pieza: `progression_mean` es un
   campo documentado de la fuente (0..9) que `coaching.py` usa como
   `factor += (progression - 4) * 0.018`. A los menores de 20 se les dio
   valoración de cantera y progresión alta al crearlos.

Con eso, un mundo que arranca en el 93-94 va soltando por sí solo a los grandes
de la segunda mitad de la década, que es exactamente lo que se busca, sin
inventar a nadie y sin que los de la primera mitad se esfumen.

**Lo que queda por decidir:**

- Si el techo histórico se saca de algún dato o se estima. Hoy no está en
  ninguna parte.
- Cuánto puede caer un veterano: sin suelo acabaría en 40 y sería otra forma de
  desaparecer.
- De dónde salen las caras nuevas si nadie se retira. La cantera queda
  descartada como fuente de gente inventada; la alternativa honesta es ir
  incorporando por temporadas a futbolistas reales que aún no están fichados.

### Otros cabos sueltos

- Un club que en Europa cayó en primera ronda tendrá plantilla de 14: hay que
  ver si da para repartir una temporada entera sin números raros.
- La progresión debe seguir usando `progression_mean`, para que un canterano de
  estos suba más rápido que un veterano igual que en el resto del mundo.

---

## 8. Decisiones pendientes

- Qué hacer con un club cuya plantilla en BDFutbol se quede en 12 o 13 fichas:
  ¿entra corto o se deja fuera?
- Si un club de los 24 actuales tiene plantilla real más corta que la inventada,
  ¿se acepta la pérdida de profundidad?

---

## 9. Estado al cerrar la sesión

**Terminado y pendiente de comprometer:**

- Pool de selecciones: 1.073 creados, 251 reconciliados, 3 homónimos apartados,
  **69 selecciones jugables**, cero identificadores duplicados, cero fichas
  preexistentes dañadas.
- **7.997 nacionalidades** asignadas desde el país de nacimiento, marcadas como
  inferencia. 462 se quedan en blanco por no tener ninguna pista. Montenegro
  apunta a Yugoslavia. Titi Camara y Mohamed Sylla corregidos de Papúa Nueva
  Guinea a Guinea.
- 18 países nuevos en el catálogo con nombre de 1993 —el 88 es **Zaire**— más 36
  que sólo tenían nombre en la fuente.
- `confederations.py`: reparto UEFA/CONMEBOL/CAF/AFC/CONCACAF/OFC con las 13+4+3+2+2
  plazas del Mundial de 24. Australia en Oceanía, que es donde jugaba en 1993.

**Defectos corregidos en las herramientas por el camino:**

1. `write_creation_registry` reescribía el registro entero y borraba 1.685 filas
   de otras tandas. Ahora manda sólo sobre sus dos orígenes.
2. Las altas del pool no eran desechables: v046 había fusionado identidades
   rusas sobre ellas y el reaplicado las dejaba desnudas.
3. Los identificadores nuevos pisaban un rango ocupado. Ahora el generador
   aborta si el inicial toca algo existente.
4. 132 nombres traían el desambiguador de Wikipedia
   (`Gheorghe Popescu (footballer, born 1967)`), que además impedía reconciliar.
5. Al unir el lote curado con el de torneos, 20 personas estaban en los dos.

**Suite:** venía de 49 → 40 → 17 → 10 fallos. La última corrección está puesta,
pero la pasada que la validaba **se paró antes de terminar**, así que no hay
resultado: el estado verde no está comprobado.

### Por dónde empezar mañana

```bash
cd c:/Users/jaric/Documents/Mister9394
PYTHONPATH=. PYTHONIOENCODING=utf-8 python -m pytest backend/tests -q
```

Tarda unos 14 minutos. El registro de creados (3.177 filas) y la cola de fotos
ya están regenerados con la corrección puesta, así que **no hace falta volver a
lanzarlos**; el universo está listo tal cual.

Si sale verde, comprometer el pool de selecciones y las nacionalidades, y de ahí
al paso 1 con el Rosenborg. Si quedan fallos, serán de la misma familia: alguna
tanda anterior escribió un campo sobre una ficha del pool y el reaplicado lo
devuelve a su valor genérico. La lista de campos a conservar está en
`CARRIED_OVER`, en `backend/tools/enrich_world_cup_1994.py`.
