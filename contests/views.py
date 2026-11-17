import datetime

from django.contrib import messages
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ContestForm, EntryForm, ThemeSongForm
from .models import Contest, Entry, ThemeSong


def _contest_by_date(date_str):
    try:
        date = datetime.date.fromisoformat(date_str)
    except ValueError:
        raise Http404("日付の形式が正しくありません")
    return get_object_or_404(Contest, date=date)


def contest_list(request):
    q = request.GET.get("q", "").strip()
    contests = Contest.objects.prefetch_related("entries__award")
    if q:
        contests = contests.filter(
            Q(entries__word__icontains=q) | Q(entries__speaker__icontains=q) | Q(entries__description__icontains=q)
        ).distinct()
    return render(
        request,
        "contests/contest_list.html",
        {
            "contests": contests,
            "q": q,
            "current_song": ThemeSong.for_date(datetime.date.today()),
        },
    )


def contest_create(request):
    form = ContestForm(request.POST or None, initial={"date": datetime.date.today()})
    if request.method == "POST" and form.is_valid():
        contest = form.save()
        messages.success(request, "大会を作成しました。流行語を登録しましょう。")
        return redirect(contest)
    return render(request, "contests/form.html", {"form": form, "title": "大会を作成"})


def contest_detail(request, date):
    contest = _contest_by_date(date)
    return render(
        request,
        "contests/contest_detail.html",
        {"contest": contest, "entries": contest.entries.select_related("award")},
    )


def contest_edit(request, date):
    contest = _contest_by_date(date)
    form = ContestForm(request.POST or None, instance=contest)
    if request.method == "POST" and form.is_valid():
        contest = form.save()
        messages.success(request, "大会を更新しました。")
        return redirect(contest)
    return render(request, "contests/form.html", {"form": form, "title": "大会を編集", "back": contest})


@require_POST
def contest_delete(request, date):
    contest = _contest_by_date(date)
    contest.delete()
    messages.success(request, f"{contest} を削除しました。")
    return redirect("contests:contest_list")


def entry_create(request, date):
    contest = _contest_by_date(date)
    form = EntryForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        entry.contest = contest
        entry.save()
        messages.success(request, f"「{entry.word}」を登録しました。")
        return redirect(contest)
    return render(
        request, "contests/form.html", {"form": form, "title": f"{contest} に流行語を登録", "back": contest}
    )


def entry_edit(request, pk):
    entry = get_object_or_404(Entry, pk=pk)
    form = EntryForm(request.POST or None, request.FILES or None, instance=entry)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"「{entry.word}」を更新しました。")
        return redirect(entry.contest)
    return render(request, "contests/form.html", {"form": form, "title": "流行語を編集", "back": entry.contest})


@require_POST
def entry_delete(request, pk):
    entry = get_object_or_404(Entry, pk=pk)
    contest = entry.contest
    entry.image.delete(save=False)
    entry.delete()
    messages.success(request, f"「{entry.word}」を削除しました。")
    return redirect(contest)


def song_list(request):
    return render(request, "contests/song_list.html", {"songs": ThemeSong.objects.all()})


def song_create(request):
    form = ThemeSongForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "テーマソングを登録しました。")
        return redirect("contests:song_list")
    return render(request, "contests/form.html", {"form": form, "title": "テーマソングを登録"})


def song_edit(request, pk):
    song = get_object_or_404(ThemeSong, pk=pk)
    form = ThemeSongForm(request.POST or None, instance=song)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "テーマソングを更新しました。")
        return redirect("contests:song_list")
    return render(request, "contests/form.html", {"form": form, "title": "テーマソングを編集"})


@require_POST
def song_delete(request, pk):
    get_object_or_404(ThemeSong, pk=pk).delete()
    messages.success(request, "テーマソングを削除しました。")
    return redirect("contests:song_list")


def ranking(request):
    """言った人ごとの受賞回数ランキング。"""
    speakers = (
        Entry.objects.values("speaker")
        .annotate(total=Count("id"))
        .order_by("-total", "speaker")
    )
    return render(request, "contests/ranking.html", {"speakers": speakers})
