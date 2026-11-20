-- Articles SAP (MARA) avec leur désignation française (MAKT, langue 'F').

with mara as (

    select * from {{ source('bronze', 'mara') }}
    qualify row_number() over (partition by MATNR order by _loaded_at desc) = 1

),

makt as (

    select MATNR, MAKTX
    from {{ source('bronze', 'makt') }}
    where SPRAS = 'F'
    qualify row_number() over (partition by MATNR order by _loaded_at desc) = 1

)

select
    mara.MATNR                              as article_id,
    makt.MAKTX                              as designation,
    mara.MTART                              as type_article,
    case mara.MTART
        when 'FERT' then 'Produit fini'
        when 'HAWA' then 'Marchandise'
        else 'Autre'
    end                                     as type_article_libelle,
    mara.MATKL                              as groupe_marchandises,
    mara.MEINS                              as unite_base,
    try_cast(mara.BRGEW as decimal(13, 3))  as poids_brut,
    mara.GEWEI                              as unite_poids,
    {{ sap_date('mara.ERSDA') }}            as date_creation,
    mara._loaded_at
from mara
left join makt on mara.MATNR = makt.MATNR
