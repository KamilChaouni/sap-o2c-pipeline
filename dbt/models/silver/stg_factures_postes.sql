-- Postes des factures (VBRP), avec les liens vers la livraison et la commande.

with source as (

    select * from {{ source('bronze', 'vbrp') }}
    qualify row_number() over (partition by VBELN, POSNR order by _loaded_at desc) = 1

)

select
    VBELN || '-' || POSNR                   as facture_poste_id,
    VBELN                                   as facture_id,
    POSNR                                   as poste,
    MATNR                                   as article_id,
    try_cast(FKIMG as decimal(13, 3))       as quantite_facturee,
    VRKME                                   as unite_vente,
    try_cast(NETWR as decimal(15, 2))       as montant_net,
    VGBEL                                   as livraison_id,
    VGBEL || '-' || VGPOS                   as livraison_poste_id,
    AUBEL                                   as commande_id,
    AUBEL || '-' || AUPOS                   as commande_poste_id,
    _loaded_at
from source
