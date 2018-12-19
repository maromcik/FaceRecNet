from django.db import models

class Person(models.Model):
    name = models.CharField(max_length=50)
    authorized = models.NullBooleanField()
    file_path = models.CharField(max_length=300)
    class Meta:
        verbose_name_plural = "persons"

class Log(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    time = models.DateTimeField('date of attempt to access')
    granted = models.NullBooleanField()
    photo_path = models.CharField(max_length=300)
    class Meta:
        verbose_name_plural = "logs"