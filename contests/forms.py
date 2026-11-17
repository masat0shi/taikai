from django import forms
from django.conf import settings

from . import hall
from .models import Award, Contest, Entry, ThemeSong

DATE_INPUT = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class AwardForm(forms.ModelForm):
    class Meta:
        model = Award
        fields = ["name", "order", "is_active"]


class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ["date", "note"]
        widgets = {"date": DATE_INPUT, "note": forms.Textarea(attrs={"rows": 2})}


class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ["award", "word", "speaker", "description", "image"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, contest, **kwargs):
        super().__init__(*args, **kwargs)
        self.contest = contest
        qs = Award.objects.filter(is_active=True)
        if self.instance.pk:  # 編集時は使用停止になった賞も選べるように
            qs = qs | Award.objects.filter(pk=self.instance.award_id)
        self.fields["award"].queryset = qs.distinct()
        self.fields["image"].help_text = f"{settings.MAX_IMAGE_SIZE // (1024 * 1024)}MB まで"

        # この大会より前に殿堂入りした人は受賞できない
        self.retired = {
            m["speaker"]: m["inducted_on"] for m in hall.hall_of_fame() if m["inducted_on"] < contest.date
        }
        if self.retired:
            self.fields["speaker"].help_text = "殿堂入りのため受賞できない人：" + "・".join(self.retired)

    def clean_speaker(self):
        speaker = self.cleaned_data["speaker"].strip()
        inducted_on = self.retired.get(speaker)
        if inducted_on:
            raise forms.ValidationError(
                f"{speaker} さんは {inducted_on:%Y.%m.%d} に殿堂入りしているため、それ以降の大会では受賞できません。"
            )
        return speaker

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and getattr(image, "size", 0) > settings.MAX_IMAGE_SIZE:
            raise forms.ValidationError(
                f"画像が大きすぎます（{settings.MAX_IMAGE_SIZE // (1024 * 1024)}MB まで）。縮小してから添付してください。"
            )
        return image


class ThemeSongForm(forms.ModelForm):
    class Meta:
        model = ThemeSong
        fields = ["title", "artist", "url", "start_date", "end_date", "note"]
        widgets = {
            "start_date": DATE_INPUT,
            "end_date": DATE_INPUT,
            "note": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        data = super().clean()
        start, end = data.get("start_date"), data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "終了日は開始日以降にしてください。")
        return data
