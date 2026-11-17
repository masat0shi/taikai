"""ジャックと殿堂入りの判定。

- ジャック: 1つの大会で、同じ人が「優勝」と「準優勝」を両方受賞すること
- 殿堂入り: ジャックを通算 HALL_OF_FAME_JACKS 回達成すること

優勝・準優勝は賞の表示順で判定する（表示順 1 = 優勝, 2 = 準優勝）。
同じ人かどうかは「言った人」の文字列（前後の空白を除く）が一致するかで判定する。
"""

from collections import defaultdict

from .models import Entry

WIN_ORDER = 1
RUNNER_UP_ORDER = 2
HALL_OF_FAME_JACKS = 2


def jackers_in(entries):
    """1大会分の受賞語からジャックした人の一覧を返す。"""
    winners, runners_up = set(), set()
    for e in entries:
        name = e.speaker.strip()
        if e.award.order == WIN_ORDER:
            winners.add(name)
        elif e.award.order == RUNNER_UP_ORDER:
            runners_up.add(name)
    return sorted(winners & runners_up)


def all_jacks():
    """{言った人: [ジャックした大会の日付, ...（古い順）]}"""
    by_contest = defaultdict(lambda: (set(), set()))
    rows = Entry.objects.filter(award__order__in=[WIN_ORDER, RUNNER_UP_ORDER]).values_list(
        "contest__date", "speaker", "award__order"
    )
    for date, speaker, order in rows:
        by_contest[date][0 if order == WIN_ORDER else 1].add(speaker.strip())

    jacks = defaultdict(list)
    for date in sorted(by_contest):
        winners, runners_up = by_contest[date]
        for name in winners & runners_up:
            jacks[name].append(date)
    return dict(jacks)


def hall_of_fame(jacks=None):
    """殿堂入りした人の一覧（殿堂入りした日が古い順）。"""
    jacks = all_jacks() if jacks is None else jacks
    members = [
        {"speaker": name, "jacks": dates, "inducted_on": dates[HALL_OF_FAME_JACKS - 1]}
        for name, dates in jacks.items()
        if len(dates) >= HALL_OF_FAME_JACKS
    ]
    return sorted(members, key=lambda m: (m["inducted_on"], m["speaker"]))
