# Míster 93/94 — V1.0-H2 Economía profunda + micro-pasada de assets

Fecha: 18-08-2026  
Base: **V1.0-H1 — economía en pesetas**  
Estado: **cerrado para esta pasada**.

## Objetivo

Profundizar la economía sin convertirla en una capa ornamental: separar capacidad de fichaje y capacidad salarial, hacer legibles los ingresos/gastos, disciplinar deuda y financiación, y demostrar que la economía se mantiene sana en carrera longitudinal. En paralelo se institucionaliza un microintento de assets en **cada** pasada de desarrollo.

## Economía implementada

Toda la economía jugable continúa expresándose en **pesetas españolas (`ESP`, `ptas.`)**.

### Presupuesto salarial real

Cada club dispone ahora de:

- presupuesto salarial anual;
- compromiso salarial anual actual;
- margen salarial disponible;
- porcentaje de presupuesto comprometido.

El presupuesto de fichajes y el salarial son restricciones diferentes. Tener caja para pagar un traspaso no permite asumir automáticamente una ficha que no cabe. Usuario, IA, renovaciones, cesiones y ofertas rivales comparten esta regla.

### Flujo de caja desglosado

Los ingresos recurrentes dejan de aparecer como una única masa comercial y pasan a distinguir:

- socios/abonos;
- televisión;
- patrocinio;
- taquilla;
- premios;
- ventas de jugadores.

Los gastos distinguen:

- salarios;
- operación del club;
- intereses de deuda;
- amortización de principal;
- compras de jugadores.

La amortización reduce deuda de verdad. Una financiación de emergencia aumenta deuda y queda registrada en `financing_draws`.

### Ingresos recurrentes sin autofinanciar malas decisiones

Los ingresos recurrentes no se recalculan a partir del salario negociado por el club. Si un club sobrepaga contratos, el balance empeora de verdad. En el cambio de temporada la base recurrente se recalibra de forma gradual hacia el coste **estructural inferido** de la plantilla, evitando a la vez que un club siga cobrando indefinidamente como si mantuviera la plantilla de 1993 cuando su escala deportiva ha cambiado mucho.

### Consejo y estrés financiero

La financiación repetida y la deuda alta reducen los presupuestos discrecionales de temporadas posteriores. El juego protege primero contratos ya firmados: no reescribe salarios existentes para cuadrar números. El castigo aparece en margen salarial futuro y presupuesto de fichajes.

### Reparación de plantilla IA económicamente segura

Se corrigió una causa concreta de espiral de deuda: el reparador de plantillas podía cubrir una emergencia de 18 jugadores seleccionando al mejor agente libre disponible, aunque su ficha fuese desproporcionada para el club.

Ahora se separan:

- **cobertura mínima obligatoria**: prioriza perfiles funcionales y asequibles;
- **profundidad/mejora aspiracional**: puede priorizar calidad, pero sólo con caja y margen salarial.

Este cambio redujo radicalmente la necesidad de financiación de emergencia en los soaks.

## UX de Economía

La pantalla expone ahora, de forma diferenciada:

- Tesorería;
- Presupuesto de fichajes;
- Margen transferible;
- Presupuesto salarial anual y % comprometido;
- Margen salarial anual;
- Masa salarial anual;
- Balance mensual;
- Deuda;
- socios/abonos, TV y patrocinio;
- operación, intereses y amortización.

La intención es que el usuario pueda distinguir inmediatamente entre **tener dinero**, **tener permiso para fichar** y **tener margen para pagar la ficha**.

## Certificación longitudinal

Se ejecutó un soak reanudable completo de 30 temporadas con el modelo H2 final.

| Horizonte | Estado | Clubes | Plantillas min/med/max | Cajas negativas | Caja máxima | Deuda máxima | Transición verano |
|---|---|---:|---:|---:|---:|---:|---:|
| 3 temporadas | healthy | 444 | 18 / 22 / 25 | 0 | 878,6 M ptas. | 545,3 M ptas. | 2,8 s |
| 10 temporadas | healthy | 444 | 18 / 21 / 25 | 0 | 1.030,7 M ptas. | 506,6 M ptas. | 3,5 s |
| 20 temporadas | warning* | 444 | 18 / 19 / 25 | 0 | 1.438,8 M ptas. | 456,1 M ptas. | 12,3 s |
| 30 temporadas | **healthy** | 444 | 18 / 18 / 25 | 0 | 1.713,0 M ptas. | 410,6 M ptas. | 4,3 s |

\* La advertencia de la temporada 20 es exclusivamente `summer_latency`; no procede de economía. La temporada 30 vuelve a `healthy`.

Resultado final de 30 temporadas:

- 444 clubes activos;
- 0 cajas negativas;
- 0 violaciones activas de presupuesto salarial;
- 0 XI IA ilegales;
- plantillas entre 18 y 25;
- caja mediana activa aproximada: **170,8 M ptas.**;
- caja máxima: **1.713,0 M ptas.**;
- deuda máxima: **410,6 M ptas.**;
- 76 clubes usaron alguna financiación al menos una vez a lo largo de 30 temporadas;
- financiación acumulada en todo el mundo durante 30 temporadas: **5.719,0 M ptas.**;
- save final: **34,48 MB**;
- historia: 30 temporadas archivadas y 870 honores registrados.

El detalle machine-readable queda en `docs/qa/V100_H2_ECONOMY_30Y_SOAK.json`.

## Gates dirigidos

- 39 tests dirigidos de economía, mercado, IA, negociación, API y cobertura: PASS;
- gates unitarios economía + IA + mercado tras los últimos ajustes: PASS;
- frontend `check:sfc`: PASS;
- frontend `check:ui`: PASS;
- frontend `check:vue`: PASS (28/28 SFCs).

## Asset micro-pass obligatorio

Desde H2 cada pasada de desarrollo debe intentar también mejorar assets, con límite pequeño y sin bloquear el frente principal si la fuente no responde.

Se añadió el comando canónico:

```bash
python backend/tools/run_asset_pass.py --limit 12 --report <ruta.json>
```

En H2:

- se revisaron/normalizaron 385 originales BDFutbol ya descargados;
- los 385 ya estaban correctamente integrados en runtime;
- se intentaron 12 descargas nuevas;
- 0 pudieron descargarse;
- las 12 fallaron por resolución DNS de BDFutbol en el entorno de ejecución;
- el fallo queda registrado y no bloquea el checkpoint.

Trazabilidad:

- `data/football9394/asset_pass_h2_normalize.json`;
- `data/football9394/asset_pass_h2_download.json`;
- `data/football9394/asset_pass_h2_summary.json`.

La regla permanente queda incorporada también a `docs/V100_H_N_STUDIO_ADVANCE_PLAN.md`.

## Decisión de cierre H2

La economía ya tiene una base jugable longitudinal mucho más robusta: la moneda, el presupuesto de fichajes, el presupuesto salarial, la caja, la deuda y los flujos mensuales representan conceptos distintos y producen restricciones reales.

El siguiente trabajo económico de mayor retorno sería calibrar con más detalle **taquilla/asistencia, premios por competición, contratos TV/patrocinio por país/nivel y objetivos financieros del consejo**, manteniendo el soak 3/10/20/30 como gate obligatorio y repitiendo el microintento de assets en la misma pasada.
