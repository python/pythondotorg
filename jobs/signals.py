from django.dispatch import Signal

# Sent after job offer was submitted for review
job_was_submitted = Signal()
# Sent after job offer was approved
job_was_approved = Signal()
# Sent after job offer was rejected
job_was_rejected = Signal()
# Sent after comment was posted
comment_was_posted = Signal()
