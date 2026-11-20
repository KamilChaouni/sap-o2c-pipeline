-- Dimension article.
-- On ajoute une ligne "INCONNU" : les ventes dont l'article n'existe pas dans
-- MARA y sont rattachées, au lieu de disparaître dans les rapports.

select
    article_id,
    designation,
    type_article,
    type_article_libelle,
    groupe_marchandises,
    unite_base,
    poids_brut,
    false as est_inconnu
from {{ ref('stg_articles') }}

union all

select
    'INCONNU'                   as article_id,
    'Article inconnu'           as designation,
    null                        as type_article,
    'Inconnu'                   as type_article_libelle,
    'INCONNU'                   as groupe_marchandises,
    null                        as unite_base,
    null                        as poids_brut,
    true                        as est_inconnu
