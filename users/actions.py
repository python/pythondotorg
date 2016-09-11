import csv

from django.http import HttpResponse


def export_csv(modeladmin, request, queryset):
    membership_name = {
        0: 'Basic', 1: 'Supporting', 2: 'Sponsor', 3: 'Managing',
        4: 'Contributing', 5: 'Fellow'
    }
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=membership.csv'
    fieldnames = [
        'membership_type', 'creator', 'email_address', 'votes',
        'last_vote_affirmation',
    ]
    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()
    for obj in queryset:
        writer.writerow({
            'membership_type': membership_name.get(obj.membership_type),
            'creator': obj.creator,
            'email_address': obj.email_address,
            'votes': obj.votes,
            'last_vote_affirmation': obj.last_vote_affirmation,
        })
    return response

export_csv.short_description = 'Export CSV'
