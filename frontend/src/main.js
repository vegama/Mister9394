import { createApp } from 'vue'
import App from './football9394/Football9394App.vue'
import './styles/core.css'
import './styles/football9394-manager.css'


const app = createApp(App)

// Football 1993-94 fork: the visual era is a product-level contract, not a
// per-screen decoration.  CSS can therefore keep every workspace in the same
// modern football management language while remaining asset-original.
if (typeof document !== 'undefined') document.documentElement.dataset.footballEra = '1993-94'

// B5-11 · Sin esto, cualquier excepción no capturada dentro de un componente
// deja la aplicación en pantalla blanca sin explicación ni forma de salir.
// Se pinta un aviso mínimo sobre el DOM en lugar de perder al usuario.
app.config.errorHandler = (err, instance, info) => {
  console.error('[Míster 93/94] error no capturado', { err, info })
  const aviso = document.getElementById('fatal-error') || (() => {
    const nodo = document.createElement('div')
    nodo.id = 'fatal-error'
    nodo.setAttribute('role', 'alert')
    nodo.style.cssText = 'position:fixed;inset:auto 0 0 0;z-index:9999;padding:12px 16px;background:#7f1d1d;color:#fff;font:14px/1.4 system-ui,sans-serif'
    document.body.appendChild(nodo)
    return nodo
  })()
  aviso.textContent = `Se ha producido un error inesperado (${info}). La partida sigue guardada en el servidor; recarga la página para continuar.`
}

app.mount('#app')
