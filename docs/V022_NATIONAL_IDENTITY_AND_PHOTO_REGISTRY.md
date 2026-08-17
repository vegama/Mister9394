# 0.22 · identidad histórica, selecciones y registro de fotos

## Objetivo

Esta pasada amplía el universo internacional 1993-94 con una regla más fuerte que “añadir jugadores”: **no se crea ningún futbolista hasta haberlo comparado contra toda la base existente**. La nacionalidad no actúa como filtro excluyente porque muchos registros legacy sólo conservan país de nacimiento o carecen de selección internacional.

## Reconciliación global

`backend/app/football9394/identity_reconciliation.py` combina nombre normalizado/transliterado, nombre propio, apellido, fecha de nacimiento, club esperado y país. Las coincidencias dudosas no se aceptan: `ambiguous_existing_candidates` detiene el importador.

El caso de control es Dmitri Popov. En 0.21 coexistían el registro histórico ID 515 (`Popov`, Racing) y una alta USA94 separada. La 0.22 reutiliza el ID 515, elimina la segunda identidad y corrige la fecha legacy 1969-02-27 a 1967-02-27. La corrección queda en `verified_data_corrections` con valor anterior, nuevo valor y procedencia BDFutbol.

La misma auditoría recuperó otras identidades USA94 que ya existían en clubes del juego pero carecían de país internacional suficiente para el matching anterior: Sergey Yuran, Terry Phelan, Paul McGrath, John Sheridan, Alan Kernaghan, Phil Babb, Tony Cascarino, Eddie McGoldrick y Alan Kelly.

## USA 94 después de deduplicar

- 528 plazas históricas, 528 IDs runtime únicos.
- 261 jugadores reutilizados de la BD.
- 267 altas reales USA94.
- 265 altas USA94 en `Otros-País` por no disponer de club activo seguro.
- 2 altas USA94 asignadas directamente a club jugable; las demás asignaciones de club que parecían “altas” en 0.21 eran en realidad jugadores ya existentes y ahora se reutilizan.

## Nuevo pool internacional 1993-94

Primer cierre de selecciones casi funcionales: Dragoje Leković (Yugoslavia), Celso Ayala (Paraguay), Alan Fettis (Irlanda del Norte), József Csábi y János Bánfi (Hungría) y Dušan Tittel (Eslovaquia).

Segundo paquete: 22 jugadores senior registrados con su selección en 1993 para Chile, Finlandia, Australia, Ghana y Argelia. Se conservan nombre, fecha, posición amplia y club del registro histórico; los atributos finos que no existen en la BD son derivados por el modelo del juego y se marcan como estimados.

Fuentes de pool 1993:

- Chile: `https://www.national-football-teams.com/country/41/1993/Chile.html`
- Finlandia: `https://www.national-football-teams.com/country/66/1993/Finland.html`
- Australia: `https://www.national-football-teams.com/country/12/1993/Australia.html`
- Ghana: `https://www.national-football-teams.com/country/72/1993/Ghana.html`
- Argelia: `https://www.national-football-teams.com/country/3/1993/Algeria.html`

De 110 candidatos de este segundo paquete, 16 se reconciliaron con IDs ya existentes y 94 requirieron alta. Con los seis del primer paquete, la capa `national_pool_1993_94` crea 100 jugadores y reutiliza 16.

## Registro permanente para BDFutbol

`backend/tools/enrich_world_cup_1994.py` mantiene:

- `data/football9394/created_players_registry.json`
- `data/football9394/created_players_registry.csv`

Sólo contienen jugadores **realmente creados**. Un jugador reconciliado con la BD existente no aparece como “nuevo”. Campos principales: `source_id`, nombre, fecha, país, posición, `team_id`/propietario, lote, fuente de identidad, `duplicate_check`, `matched_existing_id`, búsqueda BDFutbol, `photo_filename` y `photo_status`.

`backend/tools/export_bdfutbol_photo_queue.py` genera una cola directamente consumible por un descargador:

- `data/football9394/bdfutbol_photo_queue.json`
- `data/football9394/bdfutbol_photo_queue.csv`

La cola actual contiene 367 altas reales y deja `bdfutbol_id` / `bdfutbol_url` vacíos para que el script de resolución/fotos pueda completarlos sin alterar la identidad interna.

## Gate anti-duplicados

`backend/tools/audit_historical_player_duplicates.py` compara todas las altas históricas contra los 10.528 jugadores base y también busca duplicados exactos entre altas generadas. El empaquetado 0.22 exige:

- `strong_or_ambiguous_collisions = []`
- `generated_exact_duplicates = []`
- importadores idempotentes por hash.

## Resultado de producto

- 49 selecciones funcionales con el criterio actual de 22 + equilibrio mínimo por líneas.
- Las cinco nuevas selecciones grandes de esta pasada cuentan además con un pool explícito de 22 futbolistas verificados en 1993.
- Los `Otros-País` no reciben protección artificial de mercado: venden, no compran ni compiten, y las reglas históricas de extranjeros siguen siendo el principal coste deportivo de fichar esos jugadores.
