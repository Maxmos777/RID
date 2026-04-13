# UUID estável por tenant para resolução via cabeçalho (padrão django-tenants-url, RID-native).

import uuid

from django.db import migrations, models


def _populate_public_tenant_ids(apps, schema_editor) -> None:
    """
    Não iterar instâncias completas: um SELECT * incluiria todas as colunas do
    estado migratório (ex.: langflow_workspace_id). Se migrações anteriores foram
    --fake sem criar essas colunas na BD, o ORM rebenta. values_list + update só
    toca em id e public_tenant_id.
    """
    Customer = apps.get_model("tenants", "Customer")
    qs = Customer.objects.filter(public_tenant_id__isnull=True).values_list(
        "pk", flat=True
    )
    for pk in qs:
        Customer.objects.filter(pk=pk).update(public_tenant_id=uuid.uuid4())


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0002_customer_langflow_service_api_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="public_tenant_id",
            field=models.UUIDField(
                null=True,
                blank=True,
                editable=False,
                db_index=True,
            ),
        ),
        migrations.RunPython(_populate_public_tenant_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="customer",
            name="public_tenant_id",
            field=models.UUIDField(
                default=uuid.uuid4,
                unique=True,
                editable=False,
                db_index=True,
                help_text="Identificador público (UUID) para cabeçalho X-Tenant-Id / resolução sem subdomínio.",
            ),
        ),
    ]
