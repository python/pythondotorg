from django.dispatch import Signal

# Sent after job offer was approved
job_was_approved = Signal(providing_args=['approving_user', 'job'])
# Sent after job offer was rejected
job_was_rejected = Signal(providing_args=['rejecting_user', 'job'])
