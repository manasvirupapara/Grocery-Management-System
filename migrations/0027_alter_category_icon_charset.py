from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0026_category_icon'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE store_category MODIFY icon VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'box';",
            reverse_sql="ALTER TABLE store_category MODIFY icon VARCHAR(10) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT 'box';"
        ),
    ]
