from django.dispatch import Signal

# sent after job offer was approved
job_was_approved = Signal(providing_args=['approving_user', 'job'])
