"""Supabase の Data API(PostgREST) から直接テーブルを読み書きされないよう RLS を有効にする。

Django はテーブル所有者(postgres)で接続するので RLS の影響を受けない。
ポリシーを1つも作らないことで、anon / authenticated ロールからは何も見えなくなる。
Postgres 以外(ローカルの SQLite)では何もしない。
"""

from django.db import migrations


def enable_rls(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != "postgresql":
        return
    with conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        for (table,) in cur.fetchall():
            cur.execute(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY')


class Migration(migrations.Migration):
    dependencies = [
        ("contests", "0002_seed_awards"),
        ("admin", "0003_logentry_add_action_flag_choices"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("sessions", "0001_initial"),
    ]
    operations = [migrations.RunPython(enable_rls, migrations.RunPython.noop)]
