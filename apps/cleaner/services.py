from django.utils import timezone

from .models import CleaningJob


class CleanerService:

    def __init__(self, job):
        self.job = job

    def process(self):
        """
        Placeholder for the future CSV cleaning engine.

        Pandas functionality will be implemented here later.
        """

        self.job.status = CleaningJob.Status.PROCESSING
        self.job.save(
            update_fields=["status", "updated_at"]
        )

        try:

            # ---------------------------------
            # FUTURE PANDAS PIPELINE
            # ---------------------------------
            #
            # df = pandas.read_csv(...)
            #
            # analyze
            # detect issues
            # clean
            # generate report
            #
            # ---------------------------------

            self.job.status = CleaningJob.Status.COMPLETED
            self.job.completed_at = timezone.now()

            self.job.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "updated_at",
                ]
            )

            return self.job

        except Exception as exc:

            self.job.status = CleaningJob.Status.FAILED
            self.job.error_message = str(exc)

            self.job.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            raise