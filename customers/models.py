from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=100)
    gender = models.CharField(
        max_length=10,
        choices=[('Male','Male'), ('Female','Female')]
    )

    def __str__(self):
        return self.name
