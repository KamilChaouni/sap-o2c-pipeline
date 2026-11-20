{#
    Convertit une date SAP 'AAAAMMJJ' en vraie date.
    '00000000', '' ou une valeur invalide -> NULL.
    Exemple : {{ sap_date('ERDAT') }} as date_creation
#}
{% macro sap_date(colonne) -%}
    case
        when {{ colonne }} is null or trim({{ colonne }}) in ('', '00000000') then null
        else try_strptime({{ colonne }}, '%Y%m%d')::date
    end
{%- endmacro %}
