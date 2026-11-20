-- Postes des commandes de vente (VBAP).

with source as (

    select * from {{ source('bronze', 'vbap') }}
    qualify row_number() over (partition by VBELN, POSNR order by _loaded_at desc) = 1

)

select
    VBELN || '-' || POSNR                   as commande_poste_id,
    VBELN                                   as commande_id,
    POSNR                                   as poste,
    MATNR                                   as article_id,
    try_cast(KWMENG as decimal(13, 3))      as quantite_commandee,
    VRKME                                   as unite_vente,
    try_cast(NETPR as decimal(15, 2))       as prix_unitaire_net,
    try_cast(NETWR as decimal(15, 2))       as montant_net,
    WAERK                                   as devise,
    nullif(trim(ABGRU), '')                 as motif_refus,
    nullif(trim(ABGRU), '') is not null     as est_refuse,
    _loaded_at
from source
