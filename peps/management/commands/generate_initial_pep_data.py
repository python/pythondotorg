from django.core.management.base import BaseCommand, CommandError

from ...models import PepStatus, PepCategory, PepType


class Command(BaseCommand):
    """ Import PSF meeting notes from old python.org site """

    def handle(self, *args, **kwargs):
        """ Generate Statuses, Types, and Categories """
        # Types
        st, _ = PepType.objects.get_or_create(
            abbreviation='S',
            name='Standards Track PEP',
        )

        it, _ = PepType.objects.get_or_create(
            abbreviation='I',
            name='Informational PEP',
        )

        pt, _ = PepType.objects.get_or_create(
            abbreviation='P',
            name='Process PEP',
        )

        # Statuses
        accepted, _ = PepStatus.objects.get_or_create(
            abbreviation='A',
            name='Accepted proposal',
        )
        rejected, _ = PepStatus.objects.get_or_create(
            abbreviation='R',
            name='Rejected proposal',
        )
        withdrawn, _ = PepStatus.objects.get_or_create(
            abbreviation='W',
            name='Withdrawn proposal',
        )
        deferred, _ = PepStatus.objects.get_or_create(
            abbreviation='D',
            name='Deferred proposal',
        )
        final, _ = PepStatus.objects.get_or_create(
            abbreviation='F',
            name='Final proposal',
        )
        active, _ = PepStatus.objects.get_or_create(
            abbreviation='A',
            name='Active proposal',
        )
        draft, _ = PepStatus.objects.get_or_create(
            abbreviation='D',
            name='Draft proposal',
        )
        superseded, _ = PepStatus.objects.get_or_create(
            abbreviation='S',
            name='Superseded proposal',
        )

        # Categories
        meta, _ = PepCategory.objects.get_or_create(
            name='Meta-PEPs (PEPs baout PEPs or Processes)',
        )
        other, _ = PepCategory.objects.get_or_create(
            name='Other Informational PEPs',
        )
        apeps, _ = PepCategory.objects.get_or_create(
            name='Accepted PEPs (accepted; may not be implemented yet)',
        )
        opeps, _ = PepCategory.objects.get_or_create(
            name='Open PEPs (under consideration)',
        )
        fpeps, _ = PepCategory.objects.get_or_create(
            name='Finished PEPs (done, implemented in code repository)',
        )
        hpeps, _ = PepCategory.objects.get_or_create(
            name='Historical Meta-PEPs and Informational PEPs',
        )
        dpeps, _ = PepCategory.objects.get_or_create(
            name='Deferred PEPs',
        )
        wpeps, _ = PepCategory.objects.get_or_create(
            name='Abandoned, Withdrawn, and Rejected PEPs',
        )
