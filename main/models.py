from django.db import models


class Query(models.Model):
    address = models.TextField()
    nominatim_display_name = models.TextField(null=True, blank=True)
    nominatim_coordinates = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return self.address


class AddressParsed(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE, null=True, blank=True, default='')
    house = models.TextField(null=True, blank=True)
    category = models.TextField(null=True, blank=True)
    near = models.TextField(null=True, blank=True)
    house_number = models.TextField(null=True, blank=True)
    road = models.TextField(null=True, blank=True)
    unit = models.TextField(null=True, blank=True)
    level = models.TextField(null=True, blank=True)
    staircase = models.TextField(null=True, blank=True)
    entrance = models.TextField(null=True, blank=True)
    po_box = models.TextField(null=True, blank=True)
    postcode = models.TextField(null=True, blank=True)
    suburb = models.TextField(null=True, blank=True)
    city_district = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    island = models.TextField(null=True, blank=True)
    state_district = models.TextField(null=True, blank=True)
    state = models.TextField(null=True, blank=True)
    country_region = models.TextField(null=True, blank=True)
    country = models.TextField(null=True, blank=True)
    world_region = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[Parsed Address] - {self.query}"