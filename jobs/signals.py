from django.dispatch import Signal

# Sent after job offer was submitted for review
job_was_submitted = Signal(providing_args=['job'])
# Sent after job offer was approved
job_was_approved = Signal(providing_args=['approving_user', 'job'])
# Sent after job offer was rejected
job_was_rejected = Signal(providing_args=['rejecting_user', 'job'])
# Sent after comment was posted
comment_was_posted = Signal(providing_args=['comment'])
