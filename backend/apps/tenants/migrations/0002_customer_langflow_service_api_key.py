# Generated manually for RID Langflow bridge (Opção C)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0001_add_langflow_workspace_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="langflow_service_api_key",
            field=models.CharField(
                blank=True,
                help_text="API key em cache do utilizador de serviço Langflow do tenant.",
                max_length=512,
                null=True,
            ),
        ),
    ]
