import datetime
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Award, Contest, Entry, ThemeSong

TMP_MEDIA = tempfile.mkdtemp()

# 1x1 の GIF 画像
GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


@override_settings(MEDIA_ROOT=TMP_MEDIA)
class TaikaiTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)

    def test_initial_awards_seeded(self):
        self.assertEqual(list(Award.objects.values_list("name", flat=True)), ["優勝", "準優勝", "審査員特別賞"])

    def test_create_contest_and_entry_with_image(self):
        res = self.client.post(reverse("contests:contest_create"), {"date": "2026-11-17", "note": ""})
        self.assertRedirects(res, "/contests/2026-11-17/")

        award = Award.objects.get(name="優勝")
        res = self.client.post(
            reverse("contests:entry_create", args=["2026-11-17"]),
            {
                "award": award.pk,
                "word": "それな",
                "speaker": "田中",
                "description": "昼休みに連発",
                "image": SimpleUploadedFile("a.gif", GIF, content_type="image/gif"),
            },
        )
        self.assertRedirects(res, "/contests/2026-11-17/")
        entry = Entry.objects.get()
        self.assertTrue(entry.image.name.endswith(".gif"))

        res = self.client.get("/contests/2026-11-17/")
        self.assertContains(res, "それな")
        self.assertContains(res, "田中")

    def test_new_award_is_selectable(self):
        Award.objects.create(name="新語賞", order=4)
        contest = Contest.objects.create(date=datetime.date(2026, 11, 17))
        res = self.client.get(reverse("contests:entry_create", args=[contest.date.isoformat()]))
        self.assertContains(res, "新語賞")

    def test_theme_song_for_date(self):
        ThemeSong.objects.create(title="A", start_date=datetime.date(2026, 1, 1), end_date=datetime.date(2026, 6, 30))
        ThemeSong.objects.create(title="B", start_date=datetime.date(2026, 7, 1))
        self.assertEqual(ThemeSong.for_date(datetime.date(2026, 3, 1)).title, "A")
        self.assertEqual(ThemeSong.for_date(datetime.date(2026, 11, 17)).title, "B")
        self.assertIsNone(ThemeSong.for_date(datetime.date(2025, 12, 31)))

    def test_song_end_before_start_rejected(self):
        res = self.client.post(
            reverse("contests:song_create"), {"title": "X", "start_date": "2026-05-01", "end_date": "2026-04-01"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertFalse(ThemeSong.objects.exists())

    def test_search_and_ranking(self):
        c = Contest.objects.create(date=datetime.date(2026, 11, 17))
        Entry.objects.create(contest=c, award=Award.objects.get(name="優勝"), word="それな", speaker="田中")
        Entry.objects.create(contest=c, award=Award.objects.get(name="準優勝"), word="エモい", speaker="田中")
        self.assertContains(self.client.get("/?q=エモ"), "エモい")
        self.assertNotContains(self.client.get("/?q=存在しない"), "それな")
        res = self.client.get(reverse("contests:ranking"))
        self.assertEqual(res.context["speakers"][0], {"speaker": "田中", "total": 2})

    @override_settings(MAX_IMAGE_SIZE=10)
    def test_oversized_image_rejected(self):
        contest = Contest.objects.create(date=datetime.date(2026, 11, 17))
        res = self.client.post(
            reverse("contests:entry_create", args=[contest.date.isoformat()]),
            {
                "award": Award.objects.first().pk,
                "word": "でかい",
                "speaker": "佐藤",
                "image": SimpleUploadedFile("a.gif", GIF, content_type="image/gif"),
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "画像が大きすぎます")
        self.assertFalse(Entry.objects.exists())

    def test_award_add_edit_delete(self):
        res = self.client.post(reverse("contests:award_create"), {"name": "新語賞", "order": 4, "is_active": "on"})
        self.assertRedirects(res, reverse("contests:award_list"))
        award = Award.objects.get(name="新語賞")

        # 使用停止にすると登録フォームの選択肢から消える
        self.client.post(reverse("contests:award_edit", args=[award.pk]), {"name": "新語賞", "order": 4}, follow=True)
        self.assertFalse(Award.objects.get(pk=award.pk).is_active)
        contest = Contest.objects.create(date=datetime.date(2026, 11, 17))
        self.assertNotContains(self.client.get(reverse("contests:entry_create", args=["2026-11-17"])), "新語賞")

        # 使われている賞は削除できない
        Entry.objects.create(contest=contest, award=award, word="w", speaker="s")
        res = self.client.post(reverse("contests:award_delete", args=[award.pk]), follow=True)
        self.assertContains(res, "削除できません")
        self.assertTrue(Award.objects.filter(pk=award.pk).exists())

        # 使われていなければ削除できる
        Entry.objects.all().delete()
        self.client.post(reverse("contests:award_delete", args=[award.pk]))
        self.assertFalse(Award.objects.filter(pk=award.pk).exists())

    def test_admin_is_gone(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    def test_bad_date_is_404(self):
        self.assertEqual(self.client.get("/contests/not-a-date/").status_code, 404)
