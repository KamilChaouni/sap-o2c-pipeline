-- Dimension client.
-- Chaque fiche SAP est conservée, avec le nom du client maître :
-- dans Power BI, regrouper sur "nom_client_maitre" fusionne les doublons.

with clients as (

    select * from {{ ref('stg_clients') }}

)

select
    c.client_id,
    c.nom_client,
    c.client_maitre_id,
    m.nom_client                as nom_client_maitre,
    c.est_doublon_potentiel,
    c.code_pays,
    coalesce(c.ville, 'Non renseignée') as ville,
    c.code_postal,
    c.groupe_comptes,
    c.date_creation,
    c.est_supprime
from clients c
left join clients m on c.client_maitre_id = m.client_id
