# v0.40.0 — Bélgica sigue abierta: Antwerp, Germinal Ekeren, Beveren y Molenbeek a perfil profundo

## Objetivo

Bélgica **no se da por cerrada** en este checkpoint. La v0.36 dejó 275 fechas de nacimiento y 248 nacionalidades internacionales pendientes; esta pasada continúa por clubes antes de abrir Rusia, priorizando identidad individual, fecha/lugar/país de nacimiento, posición real, medidas y enlace BDFutbol para foto.

La política es deliberadamente conservadora: una fuente moderna no puede retroproyectar automáticamente un Estado sucesor, una ciudadanía posterior o una posición genérica sobre 1993-94. Los conflictos quedan auditados y las posiciones no demostrables permanecen `broad_only`.

## Clubes profundizados

### Royal Antwerp

- Se recuperan 22 fechas de nacimiento y 15 nacionalidades pendientes.
- Se incorpora a **Stevan Stojanović** como miembro documentado de la plantilla 1993-94 aunque no tenga fila liguera en la tabla BDFutbol usada por staging; sus estadísticas ligueras se mantienen a cero con `league_row_absent=true`, sin inventar minutos.
- **Zsolt Muzsnay** no se incorpora porque las fuentes consultadas no permiten resolver con seguridad el conflicto de pertenencia/temporada.
- Se documenta el conflicto de fecha de **Ronny Van Rethy** y se conserva 21/11/1961 al estar respaldado por múltiples fuentes.
- Se corrigen roles de plantilla cuando la fuente especializada lo permite y se dejan tres casos amplios/conflictivos en revisión.

### Germinal Ekeren

- Los 25 jugadores del staging tienen correspondencia en la plantilla histórica consultada.
- Se recuperan 24 fechas, 20 nacionalidades, 20 países de nacimiento, 14 alturas y 10 pesos.
- **Ngoy N'Sumbu** queda asociado a **Zaire** en el contexto de 1993-94; no se retroproyecta la etiqueta moderna RD Congo.
- Se evita conflar a **Juha Jussila** con Jani Jussila: la identidad de Juha permanece separada y el conflicto de fuentes queda explícito.
- 22 perfiles cambian de rol respecto a inferencias anteriores; los casos sin especialización fiable permanecen revisables.

### Beveren

- Se cierran las 22 fechas y 22 nacionalidades que seguían pendientes en el club.
- Se corrigen 17 roles anteriores.
- **Yves Essende-Liombi** usa **Zaire** como identidad estatal histórica de 1993-94.
- **Tomas Daumantas** usa **Lituania** como nacionalidad primaria válida en 1993; Bélgica se conserva sólo como ciudadanía secundaria cuando procede.
- **Dirk Volckerick** mantiene clasificación de líbero con `source_conflict_review`: BDFutbol lo etiqueta de forma más amplia/diferente y Transfermarkt lo sitúa como sweeper en temporadas adyacentes.

### Molenbeek

- Los 25 registros del staging quedan enlazados a perfiles BDFutbol individuales.
- Se cierran 24 fechas y 22 nacionalidades pendientes.
- Se corrigen 18 roles respecto a las inferencias previas.
- Las dos filas `Laeremans` se resuelven como dos personas distintas: **Steve Laeremans** (26/02/1972, lateral derecho) y **Michael Laeremans** (18/01/1971, defensor).
- **Thierry Rouyr** pasa de central inferido a lateral izquierdo; **Daniel Nassen** a lateral derecho; **Guy Vandersmissen** a interior derecho; **Daniel Camus** a mediocentro defensivo; **Marc Wuyts** y **Rubenilson** a mediapunta; **Emil Lörincz** a líbero.
- **Alain Mvienna Ossomo** deja la inferencia de delantero y queda como centrocampista amplio.
- **Harold Deglas** y **Didier Albert** dejan posiciones defensivas/de banda inferidas y pasan a delantero amplio según su perfil histórico.
- En **Mark Williams**, BDFutbol coincide en fecha, nacionalidad sudafricana, altura/peso y condición de delantero, pero muestra Rio de Janeiro como lugar de nacimiento. Se corrige a **Cape Town** al existir fuentes biográficas sudafricanas concordantes y el conflicto queda registrado.
- **Rubenilson** mantiene Brasil como identidad histórica primaria y Bélgica como secundaria; no se fuerza una ciudadanía moderna/posterior como primaria de 1993.

## Resultado acumulado de la tanda v0.36 → v0.40

| Hueco belga | Inicio v0.36 | v0.40 | Cerrados |
|---|---:|---:|---:|
| Fecha de nacimiento | 275 | **183** | **92** |
| Nacionalidad internacional | 248 | **169** | **79** |
| País de nacimiento | 268 | **194** | **74** |
| Altura | 322 | **262** | **60** |
| Peso | 369 | **330** | **39** |

Jugadores belgas activos: **414**. El único crecimiento neto de esta tanda es la incorporación documentada de Stojanović; el resto es profundización/corrección de identidades ya existentes.

`profile_review_required` sube hasta **38** porque se ha sustituido precisión inventada por estados explícitos `broad_only`/conflictivos. Esto es intencionado: un hueco reconocido es preferible a una posición falsa.

## Qué sigue abierto en Bélgica

Bélgica continúa en trabajo. Los mayores bloques pendientes por identidad/fecha/nacionalidad son ahora:

- **Genk** — 23 fechas / 21 nacionalidades.
- **Waregem** — 23 / 20.
- **Lommel** — 21 / 21.
- **RFC Liège** — 19 / 19.
- **Cercle Brugge** — 20 / 18.
- **Oostende** — 19 / 18.
- **KV Mechelen** — 20 / 18.
- **Gent** — 21 / 16.
- **Lierse** — 18 / 17.

Los clubes ya profundizados todavía pueden conservar huecos de altura/peso o posiciones amplias cuando la fuente individual no ofrece esos datos; no se inventarán para convertir el contador en cero.

## Rusia queda deliberadamente después

No se abre aún el bloque ruso. La pasada rusa debe introducir desde el principio una desambiguación de Estado histórico más fuerte que la de un importador moderno:

1. separar **lugar de nacimiento histórico** de **nacionalidad/selección en 1993**;
2. no convertir automáticamente “USSR” en Rusia;
3. distinguir Rusia, Ucrania, Bielorrusia, Georgia, Armenia, Azerbaiyán, Kazajistán, Uzbekistán, Kirguistán, Tayikistán, Turkmenistán, Moldavia y las repúblicas bálticas según independencia, ciudadanía y selección efectiva en 1993;
4. conservar texto histórico cuando la fuente sólo demuestra “URSS” sin permitir asignar un sucesor;
5. bloquear fusiones por apellido/transliteración (cirílico/latino) sin fecha, club y perfil suficientes;
6. registrar transliteraciones/alias como evidencia de identidad, no como duplicados nuevos.

## Artefactos de esta pasada

- `backend/tools/enrich_belgium_antwerp_v037.py`
- `backend/tools/enrich_belgium_germinal_v038.py`
- `backend/tools/enrich_belgium_beveren_v039.py`
- `backend/tools/enrich_belgium_molenbeek_v040.py`
- tests específicos v0.37, v0.38, v0.39 y v0.40
- auditorías de perfiles/gaps/biografías/conflictos v0.37-v0.40
- registry y cola de fotos sincronizados mediante gates de identidad versionados

La regresión específica acumulada v0.36-v0.40 + reconciliación de identidad termina **26/26 PASS**.

## Regla de continuidad

El siguiente checkpoint debe seguir con **Genk → Waregem → Lommel** (o el orden que maximice fuentes fiables recuperadas) y continuar reduciendo Bélgica por clubes. Rusia sólo entra cuando este frente belga esté suficientemente cerrado y con los residuales documentados, para poder dedicar una pasada específica y más estricta a URSS/ex-URSS.
