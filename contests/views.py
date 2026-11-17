import datetime

from django.contrib import messages
from django.db.models import Count, Max, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import hall
from .forms import AwardForm, ContestForm, EntryForm, ThemeSongForm
from .models import Award, Contest, Entry, ThemeSong


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
    contests = list(contests)
    for c in contests:
        c.jackers = hall.jackers_in(c.entries.all())
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
    entries = list(contest.entries.select_related("award"))
    jackers = hall.jackers_in(entries)
    inducted = []
    if jackers:
        # この大会のジャックで殿堂入りした人（＝この日がちょうど規定回数目のジャック）
        jacks = hall.all_jacks()
        inducted = [
            name for name in jackers
            if len(jacks.get(name, [])) >= hall.HALL_OF_FAME_JACKS
            and jacks[name][hall.HALL_OF_FAME_JACKS - 1] == contest.date
        ]
    return render(
        request,
        "contests/contest_detail.html",
        {"contest": contest, "entries": entries, "jackers": jackers, "inducted": inducted},
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
    form = EntryForm(request.POST or None, request.FILES or None, contest=contest)
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
    form = EntryForm(request.POST or None, request.FILES or None, instance=entry, contest=entry.contest)
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
    return render(
        request, "contests/song_list.html", {"songs": ThemeSong.objects.all(), "today": datetime.date.today()}
    )


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


def award_list(request):
    awards = Award.objects.annotate(entry_count=Count("entries"))
    return render(request, "contests/award_list.html", {"awards": awards})


def award_create(request):
    next_order = (Award.objects.aggregate(m=Max("order"))["m"] or 0) + 1
    form = AwardForm(request.POST or None, initial={"order": next_order})
    if request.method == "POST" and form.is_valid():
        award = form.save()
        messages.success(request, f"賞「{award}」を追加しました。")
        return redirect("contests:award_list")
    return render(request, "contests/form.html", {"form": form, "title": "賞を追加"})


def award_edit(request, pk):
    award = get_object_or_404(Award, pk=pk)
    form = AwardForm(request.POST or None, instance=award)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"賞「{award}」を更新しました。")
        return redirect("contests:award_list")
    return render(request, "contests/form.html", {"form": form, "title": "賞を編集"})


@require_POST
def award_delete(request, pk):
    award = get_object_or_404(Award, pk=pk)
    if award.entries.exists():
        messages.error(request, f"賞「{award}」は流行語で使われているため削除できません。代わりに「使用中」を外してください。")
    else:
        award.delete()
        messages.success(request, f"賞「{award}」を削除しました。")
    return redirect("contests:award_list")


def ranking(request):
    """言った人ごとの受賞回数ランキング。"""
    speakers = (
        Entry.objects.values("speaker")
        .annotate(total=Count("id"), wins=Count("id", filter=Q(award__order=1)))
        .order_by("-total", "-wins", "speaker")
    )
    jacks = hall.all_jacks()
    speakers = list(speakers)
    for s in speakers:
        s["jacks"] = len(jacks.get(s["speaker"].strip(), []))
        s["hof"] = s["jacks"] >= hall.HALL_OF_FAME_JACKS
    return render(request, "contests/ranking.html", {"speakers": speakers})


def hall_of_fame(request):
    jacks = hall.all_jacks()
    members = hall.hall_of_fame(jacks)
    # 殿堂入りまであと少しの人（ジャック 1 回以上・未殿堂入り）
    contenders = sorted(
        (
            {"speaker": name, "jacks": dates, "remaining": hall.HALL_OF_FAME_JACKS - len(dates)}
            for name, dates in jacks.items()
            if len(dates) < hall.HALL_OF_FAME_JACKS
        ),
        key=lambda c: (c["remaining"], c["jacks"][-1]),
    )
    return render(
        request,
        "contests/hall_of_fame.html",
        {"members": members, "contenders": contenders, "required": hall.HALL_OF_FAME_JACKS},
    )
