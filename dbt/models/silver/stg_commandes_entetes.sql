-- En-têtes des commandes de vente (VBAK).

with source as (

    select * from {{ source('bronze', 'vbak') }}
    qualify row_number() over (partition by VBELN order by _loaded_at desc) = 1

)

select
    VBELN                                   as commande_id,
    {{ sap_date('ERDAT') }}                 as date_commande,
    AUART                                   as type_commande,
    case AUART
        when 'TA' then 'Commande standard'
        when 'SO' then 'Commande urgente'
        else 'Autre'
    end                                     as type_commande_libelle,
    VKORG                                   as organisation_commerciale,
    VTWEG                                   as canal_distribution,
    SPART                                   as division,
    KUNNR                                   as client_id,
    try_cast(NETWR as decimal(15, 2))       as montant_net,
    WAERK                                   as devise,
    {{ sap_date('VDATU') }}                 as date_livraison_souhaitee,
    _loaded_at
from source
