{#
    Test générique : la colonne ne doit contenir que des valeurs >= 0.
    Utilisation dans un .yml :
        data_tests:
          - valeur_positive
#}
{% test valeur_positive(model, column_name) %}

select *
from {{ model }}
where {{ column_name }} < 0

{% endtest %}
