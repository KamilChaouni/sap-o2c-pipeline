-- Un poste facturé doit avoir été livré, et on ne facture pas plus que livré.

select
    commande_poste_id,
    quantite_livree,
    quantite_facturee
from {{ ref('fait_ventes') }}
where quantite_facturee > quantite_livree
