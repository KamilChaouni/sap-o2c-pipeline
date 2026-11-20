-- En-têtes des livraisons (LIKP).

with source as (

    select * from {{ source('bronze', 'likp') }}
    qualify row_number() over (partition by VBELN order by _loaded_at desc) = 1

)

select
    VBELN                                   as livraison_id,
    {{ sap_date('ERDAT') }}                 as date_creation,
    LFART                                   as type_livraison,
    KUNNR                                   as client_id,
    {{ sap_date('WADAT_IST') }}             as date_sortie_marchandises,
    VSTEL                                   as point_expedition,
    _loaded_at
from source
