{#
    Les indicateurs SAP valent 'X' (vrai) ou vide (faux).
    Exemple : {{ sap_flag('LOEVM') }} as est_supprime
#}
{% macro sap_flag(colonne) -%}
    coalesce(trim({{ colonne }}) = 'X', false)
{%- endmacro %}
