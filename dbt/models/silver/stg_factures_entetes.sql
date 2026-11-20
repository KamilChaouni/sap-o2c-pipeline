-- En-têtes des factures (VBRK).

with source as (

    select * from {{ source('bronze', 'vbrk') }}
    qualify row_number() over (partition by VBELN order by _loaded_at desc) = 1

)

select
    VBELN                                   as facture_id,
    FKART                                   as type_facture,
    {{ sap_date('FKDAT') }}                 as date_facture,
    KUNRG                                   as client_id,
    try_cast(NETWR as decimal(15, 2))       as montant_net,
    WAERK                                   as devise,
    {{ sap_flag('FKSTO') }}                 as est_annulee,
    _loaded_at
from source
