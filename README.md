# Míster 93/94

Manager de fútbol histórico centrado en la temporada 1993-94 y en carreras persistentes multitemporada.

## Estado · checkpoint 0.3.1

El repo contiene únicamente el dominio de fútbol Míster 93/94, su frontend, tests, snapshot normalizado y los gráficos históricos usados por las entidades del mundo activo.

Este checkpoint añade el primer bloque del plan de producto:

- avance diario mundial mucho más barato mediante simulación de fondo determinista;
- Nueva carrera con selección real de liga y club y contexto antes de firmar;
- Inicio convertido en bandeja del mánager con objetivo, confianza, forma, moral, bajas y decisiones;
- once y convocatoria persistentes que consume el motor;
- gráficos históricos de `1993.zip` integrados de forma compacta;
- ficha de jugador preparada para retratos 40×55 pequeños, con jerarquía de manager clásico;
- continuidad multitemporada 93-94 → 94-95 → 95-96 conservada.

El plan completo está en `docs/MASTER_GAME_PLAN.md` y el cierre de este bloque en `docs/BLOCK_01_FOUNDATION_GAMEPLAY.md`.

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

La build de producción requiere que las dependencias npm estén ya disponibles o que el entorno tenga acceso al registro de npm.

## Datos

El runtime consume `data/football9394/historical_snapshot.json`. La MDB fuente completa se usa para trazabilidad/verificación y no se duplica en el repo limpio. Los clubes fuera del selector de carrera pueden seguir existiendo en el universo cuando una competición o la historia los necesita.
