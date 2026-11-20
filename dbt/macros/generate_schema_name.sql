{#
    Par défaut, dbt nomme les schémas "<schéma_cible>_<schéma_perso>" (ex : main_silver).
    Cette macro utilise directement le nom choisi : silver, gold.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
