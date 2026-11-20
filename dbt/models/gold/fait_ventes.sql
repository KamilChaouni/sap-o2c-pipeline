-- Table de faits des ventes.
-- Grain : une ligne par poste de commande (VBAP), enrichie avec ce qui a été
-- livré (LIPS/LIKP) et facturé (VBRP/VBRK, hors factures annulées).

with postes as (

    select * from {{ ref('stg_commandes_postes') }}

),

entetes as (

    select * from {{ ref('stg_commandes_entetes') }}

),

articles as (

    select article_id from {{ ref('stg_articles') }}

),

-- Un poste de commande peut être livré en plusieurs fois : on agrège.
livraisons as (

    select
        lp.commande_poste_id,
        sum(lp.quantite_livree)             as quantite_livree,
        max(le.date_sortie_marchandises)    as date_livraison
    from {{ ref('stg_livraisons_postes') }} lp
    join {{ ref('stg_livraisons_entetes') }} le using (livraison_id)
    group by 1

),

-- Idem pour la facturation, en excluant les factures annulées.
factures as (

    select
        fp.commande_poste_id,
        sum(fp.quantite_facturee)           as quantite_facturee,
        sum(fp.montant_net)                 as montant_facture,
        max(fe.date_facture)                as date_facture
    from {{ ref('stg_factures_postes') }} fp
    join {{ ref('stg_factures_entetes') }} fe using (facture_id)
    where not fe.est_annulee
    group by 1

)

select
    -- clés
    p.commande_poste_id,
    p.commande_id,
    p.poste,
    e.client_id,
    case when a.article_id is null then 'INCONNU' else p.article_id end as article_id,
    p.article_id                                        as article_id_sap,  -- valeur d'origine

    -- dates (liées à dim_date)
    e.date_commande,
    l.date_livraison,
    f.date_facture,

    -- mesures
    p.quantite_commandee,
    p.prix_unitaire_net,
    p.montant_net                                       as montant_commande,
    coalesce(l.quantite_livree, 0)                      as quantite_livree,
    coalesce(f.quantite_facturee, 0)                    as quantite_facturee,
    coalesce(f.montant_facture, 0)                      as montant_facture,

    -- délais en jours
    datediff('day', e.date_commande, l.date_livraison)  as delai_livraison_jours,
    datediff('day', e.date_commande, f.date_facture)    as delai_facturation_jours,

    -- statut du poste dans le flux Order-to-Cash
    case
        when p.est_refuse                                       then 'Refusé'
        when l.commande_poste_id is null                        then 'Non livré'
        when f.commande_poste_id is null                        then 'Livré non facturé'
        when f.quantite_facturee < p.quantite_commandee         then 'Facturé partiellement'
        else 'Facturé'
    end                                                 as statut,

    e.type_commande_libelle,
    e.devise
from postes p
join entetes e using (commande_id)
left join articles a on p.article_id = a.article_id
left join livraisons l on p.commande_poste_id = l.commande_poste_id
left join factures f on p.commande_poste_id = f.commande_poste_id
