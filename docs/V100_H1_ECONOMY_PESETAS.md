# V1.0-H1 · Economía en pesetas 1993-94

## Objetivo

H1 abre el plan V1.0-H→N por la economía. El runtime usa **pesetas españolas (ESP)** como moneda canónica de juego y distingue tres conceptos que antes se confundían:

1. **Presupuesto fuente** (`source_budget`): el valor histórico/importado de la base. Se conserva sin reescribirlo.
2. **Tesorería** (`cash`): liquidez operativa del club.
3. **Presupuesto de fichajes** (`transfer_budget_total` / `transfer_budget_remaining`): sobre específico de mercado.

La UI muestra `ptas.` y explica esta separación. No hay conversión a euros ni una segunda moneda de gameplay.

## Hallazgo que motivó el cambio

El campo fuente `Presupuesto` tiene convenciones muy diferentes según país/competición. Antes se usaba directamente como caja total. Eso producía casos como clubes con 300.000–500.000 ptas. de caja inicial frente a plantillas cuya masa salarial anual inferida era de decenas o más de cien millones de pesetas.

La comprobación histórica confirma además que ese campo no puede interpretarse como presupuesto anual del club. Una retrospectiva de *El País* sitúa el presupuesto del FC Barcelona 1993-94 en **7.100 M ptas.**, mientras el snapshot aporta 360,526 M; para el Real Madrid 1993-94 se publicaron **6.500 M ptas.** de presupuesto y una auditoría posterior registró más de **4.000 M ptas.** de ingresos de explotación del primer equipo y **1.044 M ptas.** invertidos en fichajes durante ese ejercicio. El snapshot aporta 525,272 M. H1 conserva esos 360/525 M como señal de mercado/fuente, no como contabilidad anual total.

El problema no estaba en la curva alta de jugadores. Dos anclas de 1993 encajan con la escala ya existente:

- Romário (rating 89): valor estimado de juego **450 M ptas.**, igual al orden de magnitud publicado para el traspaso PSV→Barcelona en julio de 1993.
- Romário (rating 89): ficha inferida **125 M ptas./año**, igual al orden de magnitud publicado al anunciar su contrato.
- La prensa española de julio de 1993 situaba aproximadamente en **25 M ptas./año** el ingreso medio de un futbolista profesional español; por tanto no se rebaja artificialmente toda la escala salarial.

H1 corrige el uso del presupuesto de club, no aplana los valores de los futbolistas.

## Normalización jugable

El presupuesto fuente se usa siempre como mínimo. Para impedir que una convención de fuente muy baja destruya el mercado del club, el presupuesto de fichajes inicial es el máximo entre:

- presupuesto fuente;
- 2 M ptas.;
- 10 % de la masa salarial anual base de la plantilla;
- 2,5 % del valor de mercado base de la plantilla.

Los importes se redondean a bloques de 50.000 ptas. cuando proceden de una regla de gameplay. **Nunca se reduce un presupuesto fuente alto.**

Ejemplos auditados sobre el snapshot del repo:

| Club | Fuente | Presupuesto fichajes H1 | Tesorería inicial | Reserva operativa | Margen utilizable inicial |
|---|---:|---:|---:|---:|---:|
| FC Barcelona | 360.526.000 | 360.526.000 | 478.776.000 | 118.250.000 | 360.526.000 |
| Real Madrid CF | 525.272.000 | 525.272.000 | 605.472.000 | 80.200.000 | 525.272.000 |
| AC Milan | 650.000.000 | 650.000.000 | 781.650.000 | 131.650.000 | 650.000.000 |
| Parma AC | 45.000.000 | 57.700.000 | 152.350.000 | 94.650.000 | 57.700.000 |
| Huracán Buceo | 400.000 | 10.700.000 | 28.900.000 | 18.200.000 | 10.700.000 |
| Arosa SC | 500.000 | 5.800.000 | 16.350.000 | 10.550.000 | 5.800.000 |

Los clubes con plantillas incompletas/no jugables mantienen un suelo conservador y se siguen reparando por los sistemas de profundidad de plantilla existentes.

Auditoría global sobre los **510 clubes con al menos 11 jugadores** del snapshot: presupuesto de fichajes H1 entre **2,1 M y 650 M ptas.**, mediana **16,475 M**; tesorería inicial entre **6,35 M y 781,65 M ptas.**, mediana **40,925 M**. El escaneo del runtime/frontend no encuentra símbolos de euro, libra o dólar como moneda jugable; la única aparición textual de `EUR` fuera del runtime económico pertenece al nombre documental `EUR-Lex` en evidencia reglamentaria griega.

## Tesorería y reserva

La tesorería inicial ya no es una copia de `Presupuesto`. El sobre de fichajes se sitúa por encima de una reserva operativa protegida, de modo que el presupuesto de mercado anunciado es realmente gastable desde el primer día sin comerse el dinero reservado para salarios, operación y deuda.

La reserva operativa objetivo equivale aproximadamente a dos meses de esos costes fijos. El dinero realmente utilizable para un fichaje es:

`min(presupuesto_fichajes_restante, tesorería - reserva_operativa)`

Por ello tener 200 M ptas. en caja no implica que las 200 M estén disponibles para fichar.

## Mercado e IA

H1 aplica el mismo límite a usuario e IA:

- búsqueda/orden de objetivos por asequibilidad;
- apertura y resolución de negociaciones;
- fichajes directos y multiday;
- primas de fichaje;
- cesiones con coste;
- ofertas rivales;
- ofertas entrantes por jugadores del usuario;
- mercado autónomo IA;
- planificación de reclutamiento.

Las ventas aumentan tesorería e, inicialmente, reinvierten el 100 % del ingreso en el sobre de mercado para conservar el comportamiento previo. Una petición de presupuesto extra aceptada por el consejo aumenta tanto la liquidez como el sobre de fichajes.

## Cambio de temporada

Cada 1 de julio se recalcula la asignación base a partir de la plantilla actual. El presupuesto no se acumula infinitamente: se conserva el mayor entre el remanente no gastado y la nueva asignación base. La caja real se conserva; no se regala liquidez nueva al hacer rollover.

## Compatibilidad de saves

Se mantiene `CAREER_SCHEMA_9394 = 23`. El cargador ya ejecuta una normalización de estado en cada carga; H1 la amplía para incorporar los nuevos campos sin borrar caja, deuda, ingresos ni gasto ya ocurridos. Los saves antiguos conservan su historia financiera y reciben únicamente la nueva semántica de presupuesto/reserva.

## UX

Economía pasa a mostrar explícitamente:

- Tesorería;
- Presupuesto de fichajes restante;
- Margen utilizable;
- Masa salarial anual;
- balance mensual;
- deuda;
- reserva operativa explicada.

Nueva carrera etiqueta el dato como **Presupuesto fichajes**, no como un ambiguo “Presupuesto”, e indica que la economía se expresa en pesetas 1993-94.

## Gates de H1

- tests unitarios de economía/mercado: 10/10 PASS;
- flujos dirigidos M7/M8/NF10/NF12 + preview de nueva carrera: 7/7 PASS;
- IA de mercado/plantilla dirigida: 8/8 PASS;
- carrera persistente + rollovers 1994-95 y 1995-96: 4/4 PASS en los gates ejecutados (incluye API de economía/negociación);
- frontend SFC/UI/Vue: PASS; `vite build` alcanza Vite pero el binario `vite` no está materializado en este entorno.


## Referencias históricas usadas para calibrar H1

- *El País*, 13-12-1997: retrospectiva económica del FC Barcelona; presupuesto 1993-94 de 7.100 M ptas.
- *El País*, 05-06-1995: retrospectiva del Real Madrid; presupuesto 1993-94 de 6.500 M ptas.
- *El País*, 21-09-1994: auditoría Price Waterhouse del Real Madrid 1993-94; deuda, ingresos de explotación, costes de personal e inversión en jugadores.
- *El País*, 17-07-1993: contrato de Romário, aproximadamente 125 M ptas. por temporada.
- *Mundo Deportivo*, 18-07-1993: operación PSV→Barcelona por Romário, 450 M ptas.
- *El País*, julio de 1993: referencia aproximada de 25 M ptas. anuales como ingreso medio de un futbolista profesional español.

Estas referencias se usan como **anclas de orden de magnitud**. H1 no presenta salarios, caja o presupuesto de cada club como contabilidad histórica exacta cuando la MDB no la contiene.
