-- Dimension calendrier : une ligne par jour.
-- Power BI a besoin d'une table de dates continue pour les calculs temporels.

with jours as (

    select unnest(generate_series(date '2024-01-01', date '2027-12-31', interval 1 day))::date as date_jour

)

select
    date_jour                                           as date_id,
    year(date_jour)                                     as annee,
    quarter(date_jour)                                  as trimestre,
    'T' || quarter(date_jour)                           as trimestre_libelle,
    month(date_jour)                                    as mois,
    case month(date_jour)
        when 1 then 'Janvier'  when 2 then 'Février'   when 3 then 'Mars'
        when 4 then 'Avril'    when 5 then 'Mai'       when 6 then 'Juin'
        when 7 then 'Juillet'  when 8 then 'Août'      when 9 then 'Septembre'
        when 10 then 'Octobre' when 11 then 'Novembre' else 'Décembre'
    end                                                 as mois_libelle,
    strftime(date_jour, '%Y-%m')                        as annee_mois,
    weekofyear(date_jour)                               as semaine_iso,
    isodow(date_jour)                                   as jour_semaine,      -- 1 = lundi
    case isodow(date_jour)
        when 1 then 'Lundi'  when 2 then 'Mardi'    when 3 then 'Mercredi'
        when 4 then 'Jeudi'  when 5 then 'Vendredi' when 6 then 'Samedi'
        else 'Dimanche'
    end                                                 as jour_libelle,
    isodow(date_jour) in (6, 7)                         as est_weekend
from jours
