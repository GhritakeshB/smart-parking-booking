from django.contrib import admin
from .models import ParkingLocation, ParkingSlot, Booking, PaymentRecord

@admin.register(ParkingLocation)
class ParkingLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'hourly_rate', 'total_floors', 'total_slots_count', 'available_slots_count', 'occupancy_rate')
    search_fields = ('name', 'city', 'address')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_number', 'location', 'floor', 'slot_type', 'status', 'price_multiplier', 'effective_hourly_rate')
    list_filter = ('location', 'floor', 'slot_type', 'status')
    search_fields = ('slot_number', 'location__name')
    list_editable = ('status',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'slot', 'driver_name', 'vehicle_number', 'start_time', 'end_time', 'total_cost', 'status')
    list_filter = ('status', 'slot__location')
    search_fields = ('booking_id', 'driver_name', 'driver_phone', 'vehicle_number')

@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'booking', 'amount', 'payment_method', 'paid_at', 'status')
    search_fields = ('transaction_id', 'booking__booking_id')
