export const MODAL_LAYERS = ['page-overlay','entity','action','confirmation','blocking','toast']
let openModals = 0
export function modalesAbiertos(){ return openModals }
export function entrarEnLaPila(){
  openModals += 1
  if(typeof document !== 'undefined') document.body.style.overflow = 'hidden'
  return openModals
}
export function salirDeLaPila(){
  openModals = Math.max(0, openModals - 1)
  if(openModals === 0 && typeof document !== 'undefined') document.body.style.overflow = ''
  return openModals
}
export function claseDeCapa(layer){ return `modal-layer-${MODAL_LAYERS.includes(layer) ? layer : 'action'}` }
