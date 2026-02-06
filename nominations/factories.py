import datetime

from django.contrib.auth.models import Group

from users.factories import UserFactory
from users.models import Membership

from .models import (
    FellowNomination,
    FellowNominationRound,
    FellowNominationVote,
)


def _create_user(username, first_name, last_name, email=None, is_staff=False):
    """Create a user with a specific username (idempotent via get_or_create pattern)."""
    from users.models import User

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "email": email or f"{username}@example.com",
            "is_staff": is_staff,
        },
    )
    if created:
        user.set_password("password")
        user.save()
    return user


def _create_round(year, quarter, is_open=True):
    """Create a FellowNominationRound with standard dates for the given quarter."""
    quarter_dates = {
        1: (datetime.date(year, 1, 1), datetime.date(year, 3, 31),
            datetime.date(year, 2, 20), datetime.date(year, 3, 20)),
        2: (datetime.date(year, 4, 1), datetime.date(year, 6, 30),
            datetime.date(year, 5, 20), datetime.date(year, 6, 20)),
        3: (datetime.date(year, 7, 1), datetime.date(year, 9, 30),
            datetime.date(year, 8, 20), datetime.date(year, 9, 20)),
        4: (datetime.date(year, 10, 1), datetime.date(year, 12, 31),
            datetime.date(year, 11, 20), datetime.date(year, 12, 20)),
    }
    start, end, cutoff, review_end = quarter_dates[quarter]
    obj, _ = FellowNominationRound.objects.get_or_create(
        year=year,
        quarter=quarter,
        defaults={
            "quarter_start": start,
            "quarter_end": end,
            "nominations_cutoff": cutoff,
            "review_start": cutoff,
            "review_end": review_end,
            "is_open": is_open,
        },
    )
    return obj


def _create_nomination(nominator, nominee_name, nominee_email, nomination_round,
                        status="pending", expiry_round=None, nominee_user=None,
                        nominee_is_fellow_at_submission=False):
    """Create a FellowNomination."""
    return FellowNomination.objects.create(
        nominator=nominator,
        nominee_name=nominee_name,
        nominee_email=nominee_email,
        nomination_statement=f"{nominee_name} has made outstanding contributions to the Python community.",
        nomination_round=nomination_round,
        status=status,
        expiry_round=expiry_round,
        nominee_user=nominee_user,
        nominee_is_fellow_at_submission=nominee_is_fellow_at_submission,
    )


def _create_fellow_membership(user, city="", country=""):
    """Create a Fellow Membership for a user if one doesn't already exist."""
    try:
        return user.membership
    except Membership.DoesNotExist:
        return Membership.objects.create(
            creator=user,
            membership_type=Membership.FELLOW,
            legal_name=f"{user.first_name} {user.last_name}",
            preferred_name=user.first_name,
            email_address=user.email,
            city=city,
            country=country,
        )


def initial_data():
    # --- Phase 1: Groups, users, rounds, nominations ---

    wg_group, _ = Group.objects.get_or_create(name="PSF Fellow Work Group")

    # WG members (Phase 1 creates 1, Phase 2 adds 3 more = 4 total)
    wg_member1 = _create_user("wg_alice", "Alice", "WGMember", "alice.wg@python.org")
    wg_member2 = _create_user("wg_bob", "Bob", "Reviewer", "bob.wg@python.org")
    wg_member3 = _create_user("wg_carol", "Carol", "Evaluator", "carol.wg@python.org")
    wg_member4 = _create_user("wg_dave", "Dave", "Assessor", "dave.wg@python.org")
    for member in [wg_member1, wg_member2, wg_member3, wg_member4]:
        member.groups.add(wg_group)

    # Staff user (not in WG group) for testing staff fallback access
    staff_user = _create_user("staff_admin", "Staff", "Admin", is_staff=True)

    # Regular nominators
    nominator1 = _create_user("nominator1", "Nominator", "One", "nominator1@example.com")
    nominator2 = _create_user("nominator2", "Nominator", "Two", "nominator2@example.com")

    # Rounds
    past_round = _create_round(2025, 3, is_open=False)      # 2025-Q3 (closed)
    current_round = _create_round(2026, 1, is_open=True)     # 2026-Q1 (open, current)
    future_round = _create_round(2026, 2, is_open=False)     # 2026-Q2 (future, empty)
    expiry_round = _create_round(2026, 4, is_open=False)     # 2026-Q4 (for expiry targets)
    old_expiry = _create_round(2025, 2, is_open=False)       # 2025-Q2 (past, for expired nom)

    # --- Past round nominations (2025-Q3) ---
    past_accepted1 = _create_nomination(
        nominator1, "Past Accepted One", "past1@example.com",
        past_round, status="accepted",
    )
    past_accepted2 = _create_nomination(
        nominator2, "Past Accepted Two", "past2@example.com",
        past_round, status="accepted",
    )
    past_not_accepted = _create_nomination(
        nominator1, "Past Not Accepted", "past_na@example.com",
        past_round, status="not_accepted",
    )

    # --- Current round nominations (2026-Q1) ---

    # 3 pending nominations
    pending1 = _create_nomination(
        nominator1, "Pending Person One", "pending1@example.com",
        current_round, status="pending", expiry_round=expiry_round,
    )
    pending2 = _create_nomination(
        nominator2, "Pending Person Two", "pending2@example.com",
        current_round, status="pending", expiry_round=expiry_round,
    )
    pending3 = _create_nomination(
        nominator1, "Pending Person Three", "pending3@example.com",
        current_round, status="pending", expiry_round=expiry_round,
    )

    # 2 under_review nominations (will have votes added in Phase 2 section)
    under_review_majority_yes = _create_nomination(
        nominator1, "Review Majority Yes", "review_yes@example.com",
        current_round, status="under_review", expiry_round=expiry_round,
    )
    under_review_majority_no = _create_nomination(
        nominator2, "Review Majority No", "review_no@example.com",
        current_round, status="under_review", expiry_round=expiry_round,
    )

    # Additional under_review for vote scenarios
    under_review_tie = _create_nomination(
        nominator1, "Review Tie Vote", "review_tie@example.com",
        current_round, status="under_review", expiry_round=expiry_round,
    )
    under_review_abstains = _create_nomination(
        nominator2, "Review All Abstain", "review_abstain@example.com",
        current_round, status="under_review", expiry_round=expiry_round,
    )
    under_review_one_vote = _create_nomination(
        nominator1, "Review One Vote", "review_onevote@example.com",
        current_round, status="under_review", expiry_round=expiry_round,
    )

    # 1 accepted in current round
    current_accepted = _create_nomination(
        nominator2, "Current Accepted", "current_accepted@example.com",
        current_round, status="accepted",
    )

    # 1 nomination where nominee is already a Fellow
    fellow_nominee_user = _create_user("already_fellow", "Already", "Fellow", "already_fellow@example.com")
    _create_fellow_membership(fellow_nominee_user, city="San Francisco", country="USA")
    already_fellow_nom = _create_nomination(
        nominator1, "Already Fellow", "already_fellow@example.com",
        current_round, status="pending", expiry_round=expiry_round,
        nominee_user=fellow_nominee_user, nominee_is_fellow_at_submission=True,
    )

    # 1 expired nomination (expiry_round in the past, still pending)
    expired_nom = _create_nomination(
        nominator2, "Expired Pending", "expired@example.com",
        past_round, status="pending", expiry_round=old_expiry,
    )

    # --- Phase 2: Votes on under_review nominations ---

    # Majority yes (3 yes, 1 no) — threshold met
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_majority_yes, voter=wg_member1,
        defaults={"vote": "yes", "comment": "Strong contributor."})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_majority_yes, voter=wg_member2,
        defaults={"vote": "yes", "comment": "Agree."})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_majority_yes, voter=wg_member3,
        defaults={"vote": "yes", "comment": "Excellent candidate."})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_majority_yes, voter=wg_member4,
        defaults={"vote": "no", "comment": "Need more info."})

    # Majority no (1 yes, 2 no, 1 abstain) — threshold not met
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_majority_no, voter=wg_member1,
        defaults={"vote": "yes", "comment": "Good work."})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_majority_no, voter=wg_member2,
        defaults={"vote": "no", "comment": "Insufficient contributions."})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_majority_no, voter=wg_member3,
        defaults={"vote": "no", "comment": "Not yet."})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_majority_no, voter=wg_member4,
        defaults={"vote": "abstain", "comment": "Conflict of interest."})

    # Tie (2 yes, 2 no) — threshold not met
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_tie, voter=wg_member1,
        defaults={"vote": "yes"})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_tie, voter=wg_member2,
        defaults={"vote": "yes"})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_tie, voter=wg_member3,
        defaults={"vote": "no"})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_tie, voter=wg_member4,
        defaults={"vote": "no"})

    # All abstains — no result
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_abstains, voter=wg_member1,
        defaults={"vote": "abstain"})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_abstains, voter=wg_member2,
        defaults={"vote": "abstain"})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_abstains, voter=wg_member3,
        defaults={"vote": "abstain"})
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_abstains, voter=wg_member4,
        defaults={"vote": "abstain"})

    # One vote cast — voting in progress
    FellowNominationVote.objects.get_or_create(
        nomination=under_review_one_vote, voter=wg_member1,
        defaults={"vote": "yes", "comment": "Looks promising."})

    # --- Phase 3: Fellow Membership records for public roster ---

    # Fellows with full profiles (some went through nomination flow)
    fellow1 = _create_user("guido_van_rossum", "Guido", "van Rossum", "guido@python.org")
    _create_fellow_membership(fellow1, city="Belmont", country="USA")

    fellow2 = _create_user("carol_willing", "Carol", "Willing", "carol@python.org")
    _create_fellow_membership(fellow2, city="San Diego", country="USA")

    fellow3 = _create_user("mariatta_wijaya", "Mariatta", "Wijaya", "mariatta@python.org")
    _create_fellow_membership(fellow3, city="Vancouver", country="Canada")

    fellow4 = _create_user("naomi_ceder", "Naomi", "Ceder", "naomi@python.org")
    _create_fellow_membership(fellow4, city="Houston", country="USA")

    fellow5 = _create_user("victor_stinner", "Victor", "Stinner", "victor@python.org")
    _create_fellow_membership(fellow5, city="", country="France")

    # Fellows without full location
    fellow6 = _create_user("brett_cannon", "Brett", "Cannon", "brett@python.org")
    _create_fellow_membership(fellow6)  # No city/country

    fellow7 = _create_user("barry_warsaw", "Barry", "Warsaw", "barry@python.org")
    _create_fellow_membership(fellow7, city="Boston", country="")  # City only

    # already_fellow_nom user already has a Fellow membership from above

    # Non-Fellow memberships (should NOT appear on roster)
    basic_user = _create_user("basic_member", "Basic", "Member", "basic@example.com")
    try:
        basic_user.membership
    except Membership.DoesNotExist:
        Membership.objects.create(
            creator=basic_user,
            membership_type=Membership.BASIC,
            legal_name="Basic Member",
            preferred_name="Basic",
            email_address=basic_user.email,
        )

    supporting_user = _create_user("supporting_member", "Supporting", "Member", "supporting@example.com")
    try:
        supporting_user.membership
    except Membership.DoesNotExist:
        Membership.objects.create(
            creator=supporting_user,
            membership_type=Membership.SUPPORTING,
            legal_name="Supporting Member",
            preferred_name="Supporting",
            email_address=supporting_user.email,
        )

    contributing_user = _create_user("contributing_member", "Contributing", "Member", "contributing@example.com")
    try:
        contributing_user.membership
    except Membership.DoesNotExist:
        Membership.objects.create(
            creator=contributing_user,
            membership_type=Membership.CONTRIBUTING,
            legal_name="Contributing Member",
            preferred_name="Contributing",
            email_address=contributing_user.email,
        )

    return {
        "groups": [wg_group],
        "wg_members": [wg_member1, wg_member2, wg_member3, wg_member4],
        "staff": [staff_user],
        "nominators": [nominator1, nominator2],
        "rounds": [past_round, current_round, future_round, expiry_round],
        "nominations": [
            past_accepted1, past_accepted2, past_not_accepted,
            pending1, pending2, pending3,
            under_review_majority_yes, under_review_majority_no,
            under_review_tie, under_review_abstains, under_review_one_vote,
            current_accepted, already_fellow_nom, expired_nom,
        ],
        "fellows": [fellow1, fellow2, fellow3, fellow4, fellow5, fellow6, fellow7, fellow_nominee_user],
    }
