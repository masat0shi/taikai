from django.db import models
from django.urls import reverse


class Award(models.Model):
    """賞の種類（優勝・準優勝・審査員特別賞など）。管理画面から追加できる。"""

    name = models.CharField("賞の名前", max_length=50, unique=True)
    order = models.PositiveIntegerField("表示順", default=100, help_text="小さいほど上に表示")
    is_active = models.BooleanField("使用中", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = verbose_name_plural = "賞"

    def __str__(self):
        return self.name


class ThemeSong(models.Model):
    """期間ごとの大会テーマソング。"""

    title = models.CharField("曲名", max_length=200)
    artist = models.CharField("アーティスト", max_length=200, blank=True)
    url = models.URLField("リンク", blank=True, help_text="YouTube などのURL")
    start_date = models.DateField("開始日")
    end_date = models.DateField("終了日", null=True, blank=True, help_text="空欄なら現在も継続中")
    note = models.TextField("メモ", blank=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = verbose_name_plural = "テーマソング"

    def __str__(self):
        return f"{self.title} / {self.artist}" if self.artist else self.title

    @classmethod
    def for_date(cls, date):
        return (
            cls.objects.filter(start_date__lte=date)
            .filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=date))
            .first()
        )


class Contest(models.Model):
    """1日分の流行語大会。"""

    date = models.DateField("開催日", unique=True)
    note = models.TextField("メモ", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = verbose_name_plural = "大会"

    def __str__(self):
        return f"{self.date:%Y-%m-%d} の大会"

    def get_absolute_url(self):
        return reverse("contests:contest_detail", args=[self.date.isoformat()])

    @property
    def theme_song(self):
        return ThemeSong.for_date(self.date)


class Entry(models.Model):
    """受賞した流行語。"""

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="entries", verbose_name="大会")
    award = models.ForeignKey(Award, on_delete=models.PROTECT, related_name="entries", verbose_name="賞")
    word = models.CharField("言葉", max_length=200)
    speaker = models.CharField("言った人", max_length=100)
    description = models.TextField("内容", blank=True, help_text="どんな状況で言われたか など")
    image = models.ImageField("画像", upload_to="entries/%Y/%m/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["award__order", "award__id", "id"]
        verbose_name = verbose_name_plural = "流行語"

    def __str__(self):
        return f"[{self.award}] {self.word}"
