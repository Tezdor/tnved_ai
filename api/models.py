from django.db import models

class ProductRequest(models.Model):
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request #{self.id}"


class ModelResult(models.Model):
    request = models.ForeignKey(
        ProductRequest,
        on_delete=models.CASCADE,
        related_name='results'
    )

    model_name = models.CharField(max_length=50)

    tnved_code = models.CharField(max_length=50)
    title = models.TextField()
    confidence = models.FloatField()
    reasoning = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)


class FinalResult(models.Model):
    request = models.OneToOneField(
        ProductRequest,
        on_delete=models.CASCADE,
        related_name='final'
    )

    recommended_code = models.CharField(max_length=50)
    confidence = models.FloatField()
    supported_by = models.JSONField(default=list)
    reasoning = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    vat = models.CharField(
    max_length=20,
    blank=True
    )

    duty = models.CharField(
        max_length=20,
        blank=True
    )