from django.db import models
from django.utils.safestring import mark_safe

class Person(models.Model):
    name = models.CharField(max_length=50)
    authorized = models.NullBooleanField()
    file = models.ImageField(upload_to="persons/")
    def __str__(self):
        return self.name
    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name_plural = "persons"


class Log(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    time = models.DateTimeField('date of attempt to access')
    granted = models.NullBooleanField()
    snapshot = models.ImageField(upload_to="snapshots/", blank=True)
    def __str__(self):
        try:
            return str(self.person.name)
        except AttributeError:
            return "unknown"
    class Meta:
        verbose_name_plural = "logs"