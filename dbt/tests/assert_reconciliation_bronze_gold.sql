-- Réconciliation : Gold doit contenir exactement les mêmes postes de commande
-- et le même montant total que la source SAP (Bronze).
-- C'est un test BLOQUANT : si des données se perdent entre Bronze et Gold,
-- la pipeline doit échouer.

with bronze as (

    select
        count(*)                                    as nb_postes,
        sum(try_cast(NETWR as decimal(15, 2)))      as montant_total
    from {{ source('bronze', 'vbap') }}

),

gold as (

    select
        count(*)                                    as nb_postes,
        sum(montant_commande)                       as montant_total
    from {{ ref('fait_ventes') }}

)

select
    bronze.nb_postes        as nb_postes_bronze,
    gold.nb_postes          as nb_postes_gold,
    bronze.montant_total    as montant_bronze,
    gold.montant_total      as montant_gold
from bronze, gold
where bronze.nb_postes <> gold.nb_postes
   or abs(bronze.montant_total - gold.montant_total) > 0.01
