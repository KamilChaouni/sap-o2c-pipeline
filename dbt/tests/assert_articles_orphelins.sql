-- Postes de commande dont l'article n'existe pas dans MARA.
-- Ils sont rattachés à l'article 'INCONNU' en Gold, mais il faut les corriger dans SAP.

{{ config(severity = 'warn') }}

select
    commande_poste_id,
    article_id_sap,
    montant_commande
from {{ ref('fait_ventes') }}
where article_id = 'INCONNU'
