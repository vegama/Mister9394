# Backlog de contenido v1.1.3

Fecha: 19-08-2026
Estado: **33 comprobaciones abiertas**, marcadas `xfail(strict=True)` en la suite.

## Qué es esto y qué no

Estas 33 comprobaciones **no son regresiones de código**. Son la especificación de un
pase de datos que se planificó, se escribió como test y se ejecutó sólo en parte.

La prueba es directa: los informes que varias de ellas exigen —
`data/football9394/database_hygiene_v113.json` y
`data/football9394/openfootball_sources_1993_94.json` — **no existen ni han existido
nunca en el repositorio**, no tienen ni un solo commit en su historial. Los tests
entraron en rojo con el mismo commit que los creó.

Mientras estuvieron mezcladas con los fallos reales, la suite no servía como
puerta: 53 rojos donde 18 eran de código y 35 eran contenido pendiente. Nadie
puede distinguir una regresión nueva dentro de ese ruido.

## Por qué `xfail(strict=True)` y no borrarlos

Marcados en estricto, funcionan como trinquete:

- la suite vuelve a estar verde y cualquier rojo nuevo **es** una regresión;
- el objetivo de datos queda escrito y no se pierde;
- cuando alguien complete una parte del pase, el test pasará y **el build avisará**
  de que hay que quitar la marca. El backlog sólo puede encogerse.

## Inventario

| Módulo | Abiertas | Qué falta |
|---|---:|---|
| `v113_database_hygiene` | 9 | El pase de higiene no se ejecutó. Objetivo: nombre visible ruso sin patronímico conservando el nombre completo, alias de retirados resueltos a la persona canónica, Popov y Radchenko como identidades únicas del Racing, y ninguna colisión de nombre visible dentro del mismo equipo. Falta su informe `database_hygiene_v113.json`. |
| `v113_uruguay_roster_coverage` | 5 | Falta el campo de identidad normalizada `historical_full_name`, las altas verificadas no están activas y Racing y Liverpool siguen con 16 efectivos en vez de 17. |
| `v113_asset_recovery_openfootball` | 4 | No se ejecutó la ingesta de fuentes openfootball (`openfootball_sources_1993_94.json`). Incluye además el cableado de retratos de entrenador en la ficha y un escudo sintético que falta. |
| `v113_vvv_roster_coverage` | 3 | VVV Venlo 1993-94 sigue con 16 jugadores en lugar de 22; las altas previstas no se crearon. |
| `v034_turkey_deep_profiles` | 3 | Profundidad de clubes turcos incompleta: efectivos, estados históricos explícitos y retratos normalizados. |
| `usa94_data_pass` | 2 | Tres contenedores `Otros-` quedaron vacíos (Países Bajos, Grecia, Turquía) al pasar sus jugadores a clubes reales; Popov sigue sin reconciliarse al Racing. |
| `v033_turkey_profiles` | 1 | Correcciones de alta confianza de Altay, Ankaragücü y Kayserispor. |
| `v044_russia_spartak_deep` | 1 | Transliteración rusa: el nombre visible conserva el patronímico. |
| `v029_profiles_and_greece_foreign_rule` | 1 | Perfiles individuales rusos sin normalizar. |
| `v042_belgium_waregem_lommel_deep` | 1 | Correcciones de rol y estado histórico de Waregem y Lommel. |
| `v030_full_rosters_and_1993_countries` | 1 | Los stagings ampliados aún producen identidades resueltas duplicadas. |
| `v024_bel_tur_rus_depth` | 1 | La puerta de plantilla de Grecia no está completa ni es única. |
| ~~`national_pool_022`~~ | ~~1~~ | **Resuelto.** El pool que se quedaba en 21 verificados lo completaron las convocatorias de torneo. La prueba vuelve a exigirse de verdad. |

## Tres grupos, tres decisiones distintas

**1. Nombres rusos con patronímico** (`v113_database_hygiene`, `v044`, `v029`).
Es lo único de esta lista que **el jugador ve**: aparecen nombres como
«Sergei Yevgenovich Gusev» donde debería leerse «Sergei Gusev», conservando el
nombre completo en la ficha. Es cosmético pero visible en plantilla, mercado y
alineación. Candidato claro a entrar en B2 junto al resto de limpieza de
interfaz.

**2. Plantillas cortas** (Uruguay, VVV, Turquía, Grecia, pools nacionales).
El propio proyecto ya lleva la cuenta en
`data/football9394/database_roster_depth_backlog_v113.json`, con la política
escrita: mínimo 18 efectivos y **sólo jugadores reales verificados de 1993-94,
nunca relleno sintético**. Es trabajo de investigación histórica, no de código, y
esa política es la razón de que siga abierto. Debe avanzar a su ritmo sin
bloquear la beta.

**3. Contenedores `Otros-` vacíos.**
Éste sí merece una decisión de producto y no de datos: son clubes que existen en
el mundo y no tienen a nadie dentro, porque sus jugadores pasaron a clubes
reales cuando se añadieron las ligas de Países Bajos, Grecia y Turquía. Lo
coherente es retirarlos, no rellenarlos.

## Cómo trabajar este backlog

```bash
# Ver sólo lo que sigue abierto
python -m pytest backend/tests -q -rx

# Al completar una parte del pase, el test pasará y el build pedirá
# quitar su marca xfail. Ésa es la señal de que el backlog ha encogido.
```
