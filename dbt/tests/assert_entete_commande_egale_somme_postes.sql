-- Le montant de l'en-tête de commande (VBAK.NETWR) doit être égal à la somme
-- des postes non refusés (VBAP.NETWR). Un écart signale une incohérence SAP.
-- Avertissement seulement : on veut le voir, sans bloquer la pipeline.

{{ config(severity = 'warn') }}

with postes as (

    select commande_id, sum(montant_net) as total_postes
    from {{ ref('stg_commandes_postes') }}
    where not est_refuse
    group by 1

)

select
    e.commande_id,
    e.montant_net                       as montant_entete,
    p.total_postes,
    e.montant_net - p.total_postes      as ecart
from {{ ref('stg_commandes_entetes') }} e
join postes p using (commande_id)
where abs(e.montant_net - p.total_postes) > 0.01
