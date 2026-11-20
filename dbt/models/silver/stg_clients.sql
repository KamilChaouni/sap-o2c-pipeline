-- Clients SAP (KNA1) nettoyés.
-- Les doublons "métier" (même société, même code postal, numéros différents)
-- ne sont pas supprimés : on les signale et on désigne un client maître.

with source as (

    select * from {{ source('bronze', 'kna1') }}
    -- si une même ligne a été chargée plusieurs fois, on garde la plus récente
    qualify row_number() over (partition by KUNNR order by _loaded_at desc) = 1

),

nettoye as (

    select
        KUNNR                                   as client_id,
        trim(NAME1)                             as nom_client,
        LAND1                                   as code_pays,
        nullif(trim(ORT01), '')                 as ville,
        PSTLZ                                   as code_postal,
        STRAS                                   as adresse,
        KTOKD                                   as groupe_comptes,
        {{ sap_date('ERDAT') }}                 as date_creation,
        {{ sap_flag('LOEVM') }}                 as est_supprime,
        -- clé de comparaison pour repérer les doublons
        upper(trim(NAME1)) || '|' || coalesce(PSTLZ, '') as cle_doublon,
        _loaded_at
    from source

)

select
    client_id,
    nom_client,
    code_pays,
    ville,
    code_postal,
    adresse,
    groupe_comptes,
    date_creation,
    est_supprime,
    -- le plus ancien numéro du groupe devient le client maître
    min(client_id) over (partition by cle_doublon)          as client_maitre_id,
    count(*) over (partition by cle_doublon) > 1            as est_doublon_potentiel,
    _loaded_at
from nettoye
