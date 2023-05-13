from django.db import models
from django.utils import timezone


# Create your models here.
class TestModelMongo(models.Model):
    name = models.CharField(max_length=200, default=None)
    age = models.IntegerField(default=None)
    created_at = models.DateTimeField(editable=True)
    modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        self.modified = timezone.now()
        return super(TestModelMongo, self).save(*args, **kwargs)

