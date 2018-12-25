from django.db import models

class Person(models.Model):
    name = models.CharField(max_length=50)
    authorized = models.NullBooleanField()
    file = models.ImageField(upload_to="persons/")
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "persons"

class Log(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    time = models.DateTimeField('date of attempt to access')
    granted = models.NullBooleanField()
    snapshot = models.ImageField(upload_to="snapshots/", default=None)
    def __str__(self):
        try:
            return str(self.person.name)+" - "+str(self.time.strftime("%d. %m. %Y, %H:%M:%S"))
        except AttributeError:
            return "unknown" + " - " + str(self.time.strftime("%d. %m. %Y, %H:%M:%S"))
    class Meta:
        verbose_name_plural = "logs"