from django.db import models
from django.utils.safestring import mark_safe


class Person(models.Model):
    name = models.CharField(max_length=50)
    authorized = models.BooleanField(default=False)
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
    granted = models.BooleanField(default=False)
    snapshot = models.ImageField(upload_to="snapshots/", blank=True)
    def __str__(self):
        try:
            return str(self.person.name)
        except AttributeError:
            return "unknown"
    class Meta:
        verbose_name_plural = "logs"

class Setting(models.Model):
    device = models.CharField(max_length=255)
    crop0 = '1'
    crop1 = '0.75'
    crop2 = '0.5'
    crop3 = '0.25'
    CROP_CHOICES = (
        (crop0, '1'),
        (crop1, '0.75'),
        (crop2, '0.5'),
        (crop3, '0.25'),
    )
    crop = models.CharField(
        max_length=10,
        choices=CROP_CHOICES,
        default=crop3,
    )
    def __str__(self):
        return "device and crop"

    class Meta:
        verbose_name_plural = "settings"