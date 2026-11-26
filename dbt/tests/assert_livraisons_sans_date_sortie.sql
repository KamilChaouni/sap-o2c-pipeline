-- Livraisons dont la date de sortie des marchandises est vide ('00000000' dans SAP).

{{ config(severity = 'warn') }}

select livraison_id, date_creation
from {{ ref('stg_livraisons_entetes') }}
where date_sortie_marchandises is null
