-- Postes des livraisons (LIPS), avec le lien vers le poste de commande.

with source as (

    select * from {{ source('bronze', 'lips') }}
    qualify row_number() over (partition by VBELN, POSNR order by _loaded_at desc) = 1

)

select
    VBELN || '-' || POSNR                   as livraison_poste_id,
    VBELN                                   as livraison_id,
    POSNR                                   as poste,
    MATNR                                   as article_id,
    try_cast(LFIMG as decimal(13, 3))       as quantite_livree,
    VRKME                                   as unite_vente,
    VGBEL                                   as commande_id,
    VGBEL || '-' || VGPOS                   as commande_poste_id,
    _loaded_at
from source
