import uuid
import secrets
from django.db import models
from django.utils import timezone

class ParkingLocation(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    city = models.CharField(max_length=100)
    address = models.TextField()
    image_url = models.URLField(blank=True, default='')
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)
    total_floors = models.IntegerField(default=3)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.city})"

    @property
    def total_slots_count(self):
        return self.slots.count()

    @property
    def available_slots_count(self):
        return self.slots.filter(status='AVAILABLE').count()

    @property
    def occupancy_rate(self):
        total = self.total_slots_count
        if total == 0:
            return 0
        occupied = self.slots.filter(status__in=['OCCUPIED', 'RESERVED']).count()
        return round((occupied / total) * 100, 1)


class ParkingSlot(models.Model):
    SLOT_TYPES = [
        ('STANDARD', 'Standard Vehicle'),
        ('COMPACT', 'Compact Car'),
        ('SUV', 'Large SUV / Truck'),
        ('EV', 'Electric Vehicle (EV) Charging'),
        ('ACCESSIBLE', 'Handicapped Accessible'),
        ('VIP', 'VIP Reserved'),
    ]

    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('RESERVED', 'Reserved'),
        ('MAINTENANCE', 'Maintenance'),
    ]

    location = models.ForeignKey(ParkingLocation, related_name='slots', on_delete=models.CASCADE)
    slot_number = models.CharField(max_length=20)
    floor = models.CharField(max_length=20, default='Floor 1')
    slot_type = models.CharField(max_length=20, choices=SLOT_TYPES, default='STANDARD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    is_covered = models.BooleanField(default=True)

    class Meta:
        unique_together = ('location', 'slot_number')
        ordering = ['floor', 'slot_number']

    def __str__(self):
        return f"{self.location.name} - Slot {self.slot_number} ({self.get_slot_type_display()})"

    @property
    def effective_hourly_rate(self):
        return round(float(self.location.hourly_rate) * float(self.price_multiplier), 2)


class Booking(models.Model):
    BOOKING_STATUS = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    booking_id = models.CharField(max_length=36, unique=True, editable=False)
    slot = models.ForeignKey(ParkingSlot, related_name='bookings', on_delete=models.CASCADE)
    driver_name = models.CharField(max_length=120)
    driver_phone = models.CharField(max_length=20)
    driver_email = models.EmailField(blank=True, default='')
    vehicle_number = models.CharField(max_length=30)
    vehicle_type = models.CharField(max_length=30, default='Sedan')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='ACTIVE')
    qr_token = models.CharField(max_length=64, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = f"PK-{uuid.uuid4().hex[:8].upper()}"
        if not self.qr_token:
            self.qr_token = secrets.token_urlsafe(16).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.booking_id} - Slot {self.slot.slot_number} ({self.vehicle_number})"


class PaymentRecord(models.Model):
    booking = models.OneToOneField(Booking, related_name='payment', on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='Digital Wallet / Card')
    paid_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='SUCCESS')

    def __str__(self):
        return f"Payment {self.transaction_id} for {self.booking.booking_id}"
