from django.db import models

# Create your models here.
class Event(models.Model):
    node_id = models.CharField(max_length=5)
    loc = models.TextField()
    temp = models.DecimalField(max_digits=5, decimal_places=2)
    hum = models.DecimalField(max_digits=5, decimal_places=2)
    light = models.DecimalField(max_digits=5, decimal_places=2)
    snd = models.DecimalField(max_digits=5, decimal_places=2)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Event #{self.id}'


class Data_Receive(models.Model):
    start = models.CharField(max_length=6)
    p_temp = models.DecimalField(max_digits=5, decimal_places=2)
    p_hum = models.DecimalField(max_digits=5, decimal_places=2)
    move =  models.CharField(max_length=4)

    def __str__(self):
        return f'Data #{self.id}'
