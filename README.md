# Míster 93/94

Manager de fútbol ambientado en la temporada 1993-94, con reglas históricas por competición, carrera persistente, mundo autónomo, mercado, economía en pesetas, selecciones, historia y transición longitudinal de temporadas.

**Versión canónica:** `1.1.2`  
**Checkpoint:** `1.1.2-rc-browser-contracts-source`  
**Estado:** responsive/zoom, navegación browser-source y red/doble envío ya tienen gates ejecutables. El bloqueo RC final es el **bundle `frontend/dist` + E2E Chromium de producción + playtest humano**.

La única fuente de versión es [`VERSION`](VERSION). Los metadatos derivados se verifican con `python backend/tools/sync_product_version.py --check` y el build frontend incluye el mismo gate.

## Ejecutar el producto

El launcher de producción es único:

```bash
python run_football9394.py
```

Sirve frontend y API desde el mismo origen y abre `http://127.0.0.1:9394`. El ZIP de release debe contener `frontend/dist`; para regenerarlo:

```bash
cd frontend
npm ci
npm run build
```

Para desarrollo sólo-API:

```bash
python run_football9394.py --dev-api --port 8000
```

Gates RC reproducibles antes del bundle final:

```bash
python backend/tools/rc_browser_matrix.py
python backend/tools/rc_navigation_history.py
cd frontend && npm run check:network && cd ..
python backend/tools/rc_production_browser_gate.py
```

El último comando sólo puede quedar verde si existe `frontend/dist`; si falta, devuelve `BLOCKED` y no se interpreta como un pase.

## Datos del usuario y recuperación

Saves, backups y logs viven fuera del repositorio. La ubicación puede personalizarse con `MISTER9394_USER_DATA_DIR`, `MISTER9394_SAVE_DIR`, `MISTER9394_BACKUP_DIR` y `MISTER9394_LOG_DIR`.

Los saves usan escritura atómica, validación antes del reemplazo, `fsync`, backup del último primario válido y recuperación automática desde backup cuando el primario está truncado o corrupto.

## Documentación canónica

- [`docs/STATUS.md`](docs/STATUS.md): estado real del producto.
- [`docs/ROADMAP.md`](docs/ROADMAP.md): cierre v1.1.x Beta / RC.
- [`docs/V110_UX_AUDIT_AND_SERIOUS_PRODUCT_PASS.md`](docs/V110_UX_AUDIT_AND_SERIOUS_PRODUCT_PASS.md): auditoría A–L y cambios de producto.
- [`docs/PLAN_V110_SERIOUS_UX_RELEASE.md`](docs/PLAN_V110_SERIOUS_UX_RELEASE.md): plan vivo de cierre UX/RC.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): arquitectura y límites técnicos.
- [`docs/QA_RELEASE.md`](docs/QA_RELEASE.md): gates de release y comandos.
- [`docs/archive/checkpoints/`](docs/archive/checkpoints/): planes, auditorías y cierres históricos preservados.

## Principios de producto

La profundidad debe llegar al usuario como decisiones futbolísticas claras, no como burocracia. La realidad histórica vive en reglas, datos y assets; la interfaz usa una gramática moderna. El mundo debe seguir sano a 3/10/20/30 temporadas y ninguna nueva expansión horizontal desplaza los gates de producto, UX, partido, mercado, arquitectura y QA.

Los assets históricos avanzan en paralelo mediante micro-pasadas auditables; un fallo de fuente no bloquea el frente principal.
