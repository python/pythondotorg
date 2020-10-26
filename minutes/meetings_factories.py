import itertools
from minutes.models import Meeting, AgendaItem, ConcernedParty, Concern


def new_psf_board_meeting(date):
    try:
        work_group_concern = Concern.objects.get(name="Work Groups")
        work_groups = work_group_concern.children_concerns.all()
    except Concern.DoesNotExist:
        work_groups = []

    directory = ConcernedParty.objects.by_concern_role("PSF", "Director")
    staff = ConcernedParty.objects.by_concern_role("PSF", "Staff")
    parties = list(itertools.chain(directory, staff))

    meeting_title = f"PSF Meeting Minutes for {date}"  # TODO format date to "Aug. 26, 2020"
    PSF_REPORTS = "Board and Staff Monthly Reports"
    WORK_GROUP_REPORTS = "Work Group Reports"
    agenda_items_title = [
        "Attendance",
        "Resolutions",
        PSF_REPORTS,
        WORK_GROUP_REPORTS,
        "Votes Approved by Email",
        "Votes Approved by Working Groups",
        "Consent Agenda Resolutions",
        "New Business",
        "Discussions",
        "Meeting Adjournment",
    ]

    meeting = Meeting.objects.create(date=date, title=meeting_title)
    meeting.parties.add(*parties)
    for title in agenda_items_title:
        AgendaItem.objects.create(meeting=meeting, title=title, content="content placeholder")
        if title == PSF_REPORTS:
            for owner in parties:
                item = AgendaItem.objects.create(meeting=meeting, title=owner.display_name, content="waiting for report")
                item.owners.add(*[owner])
        elif title == WORK_GROUP_REPORTS:
            for work_group in work_groups:
                item = AgendaItem.objects.create(meeting=meeting, title=work_group.name, content="waiting for work group report")
                item.owners.add(*ConcernedParty.objects.by_concern(work_group.name))


    return meeting
