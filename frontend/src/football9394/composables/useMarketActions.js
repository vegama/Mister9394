import { football9394Api } from '../api.js'

/**
 * Operaciones de mercado: búsqueda, seguimiento, informes, consultas,
 * negociación y salidas.
 *
 * Se extraen de `Football9394App.vue` para devolver el componente raíz por
 * debajo del presupuesto de tamaño que vigila
 * `test_m_source_roots_are_materially_smaller_and_have_real_seams`, siguiendo
 * la misma costura que el resto de composables del directorio.
 *
 * Todas comparten la misma forma: llamar a la API, aplicar el estado de
 * carrera devuelto y contar al usuario qué ha pasado.
 */
export function useMarketActions(ctx) {
  const {
    careerId, targets, selectedTarget, selectedPlayer,
    marketQuery, marketPosition, marketFreeAgents, marketWatchedOnly,
    transferFee, transferSalary, transferYears, transferSquadRole,
    transferSigningBonus, transferReleaseClause, transferDealType, transferLoanWageShare,
    applyCareerState, refreshCareerData, flash, persistMarketWorkspace,
    historicalPlayerPhoto, historicalClubCrest, formatSourceMoney, formatDateShort,
  } = ctx

  async function searchMarket(){
   if(!careerId.value)return
   try{const rows=await football9394Api.careerMarket(careerId.value,{query:marketQuery.value,limit:30,position:marketPosition.value,freeAgents:marketFreeAgents.value,watched:marketWatchedOnly.value});targets.value=rows.map(p=>[p.display_name,p.position,p.team_name||'Libre',p.overall??'—',p.estimated_transfer_value??p.market?.market_value??0,p.id,p]);persistMarketWorkspace()}catch(error){flash(`Búsqueda fallida: ${error.message}`)}
  }
  async function toggleWatch(target){
   try{const watched=!Boolean(target[6]?.watched);const result=await football9394Api.watchPlayer(careerId.value,target[5],watched);applyCareerState(result.career);target[6].watched=watched;flash(watched?'Añadido a seguimiento.':'Eliminado del seguimiento.')}catch(error){flash(`No se pudo actualizar seguimiento: ${error.message}`)}
  }

  async function scoutMarketPlayer(playerOrTarget){
   if(!careerId.value)return
   const id=Number(Array.isArray(playerOrTarget)?playerOrTarget[5]:playerOrTarget?.id)
   if(!id)return
   try{
    const result=await football9394Api.scoutPlayer(careerId.value,id)
    applyCareerState(result.career)
    if(selectedPlayer.value?.id===id){
     const detail=await football9394Api.careerPlayer(careerId.value,id)
     selectedPlayer.value={...detail,photo_url:historicalPlayerPhoto(detail.id),team_crest_url:historicalClubCrest(detail.team_id),market_value_display:detail.transfer_value_is_exact?formatSourceMoney(detail.estimated_transfer_value):`≈ ${formatSourceMoney(detail.estimated_transfer_value)}`}
    }
    await searchMarket()
    flash(`Informe encargado · previsto ${formatDateShort(result.assignment.due_on)}.`)
   }catch(error){flash(`No se pudo encargar el informe: ${error.message}`)}
  }
  async function inquireMarketPlayer(playerOrTarget){
   if(!careerId.value)return
   const id=Number(Array.isArray(playerOrTarget)?playerOrTarget[5]:playerOrTarget?.id)
   if(!id)return
   try{const result=await football9394Api.marketInquiry(careerId.value,id);applyCareerState(result.career);flash(`Consulta: ${result.inquiry.note}`)}catch(error){flash(`No se pudo consultar: ${error.message}`)}
  }
  async function withdrawNegotiation(row){
   try{const result=await football9394Api.withdrawNegotiation(careerId.value,row.id);applyCareerState(result.career);flash('Negociación retirada.')}catch(error){flash(`No se pudo retirar: ${error.message}`)}
  }
  async function submitTransfer(){
   if(!selectedTarget.value||!careerId.value)return
   try{const result=await football9394Api.openNegotiation(careerId.value,{playerId:selectedTarget.value[5],feeOffer:Number(transferFee.value),salaryOffer:Number(transferSalary.value),contractYears:Number(transferYears.value),squadRole:transferSquadRole.value,signingBonus:Number(transferSigningBonus.value||0),releaseClause:transferReleaseClause.value?Number(transferReleaseClause.value):null,dealType:transferDealType.value,loanWageShare:Number(transferLoanWageShare.value||0)});applyCareerState(result.career);selectedTarget.value=null;persistMarketWorkspace();flash(`Oferta enviada · respuesta prevista ${result.negotiation.response_date}`)}catch(error){flash(`Negociación fallida: ${error.message}`)}
  }
  async function counterNegotiation(row){
   try{const result=await football9394Api.counterNegotiation(careerId.value,row.id,{feeOffer:Number(row.counter_fee??row.fee_offer),salaryOffer:Number(row.counter_salary??row.salary_offer),contractYears:Number(row.contract_years||3),loanWageShare:row.deal_type==='loan'?Number(row.counter_wage_share??row.loan_wage_share??100):null});applyCareerState(result.career);flash(`Contraoferta enviada · respuesta ${result.negotiation.response_date}`)}catch(error){flash(`No se pudo responder: ${error.message}`)}
  }
  async function toggleTransferListing(row){
   try{const listed=Boolean(row.profile?.transfer_listed);const result=listed?await football9394Api.unlistPlayer(careerId.value,row.id):await football9394Api.listPlayer(careerId.value,row.id,Number(row.profile?.estimated_transfer_value||0));applyCareerState(result.career);flash(listed?'Jugador retirado del mercado.':'Jugador puesto en el mercado.')}catch(error){flash(`No se pudo cambiar su situación: ${error.message}`)}
  }
  async function acceptIncomingOffer(offer){
   try{const result=await football9394Api.acceptIncomingOffer(careerId.value,offer.id);applyCareerState(result.career);await refreshCareerData(result.career);flash(`Venta cerrada por ${formatSourceMoney(result.transfer.fee)}`)}catch(error){flash(`No se pudo aceptar: ${error.message}`)}
  }

  return {
    searchMarket, toggleWatch, scoutMarketPlayer, inquireMarketPlayer,
    withdrawNegotiation, submitTransfer, counterNegotiation,
    toggleTransferListing, acceptIncomingOffer,
  }
}
