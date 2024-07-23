from django.db import models

class FinancialData(models.Model):
    client_name = models.CharField(max_length=255)
    advisor_name = models.CharField(max_length=255)
    assets = models.JSONField()
    expenditures = models.JSONField()
    income = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client_name} - {self.advisor_name}"
