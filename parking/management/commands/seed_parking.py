from django.core.management.base import BaseCommand
from parking.models import ParkingLocation, ParkingSlot, Booking, PaymentRecord

class Command(BaseCommand):
    help = 'Resets all slots to AVAILABLE (Green) and clears all previous bookings for a fresh start.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Resetting Grand Shopping Mall Parking Database for fresh start...'))

        # Clear old mock bookings and payments
        PaymentRecord.objects.all().delete()
        Booking.objects.all().delete()

        # Create/Get Mall Location
        mall, created = ParkingLocation.objects.get_or_create(
            slug='grand-shopping-mall',
            defaults={
                'name': 'Grand Shopping Mall Parking Deck',
                'city': 'Central Metro District',
                'address': '101 Commercial Boulevard, Sector 4',
                'hourly_rate': 50.00,
                'total_floors': 4,
                'image_url': 'https://images.unsplash.com/photo-1590674899484-d5640e854abe?auto=format&fit=crop&w=1200&q=80',
                'description': 'Multi-story smart mall parking deck with automated gate registration and attendant monitoring.'
            }
        )

        floors = ['Ground Floor', 'Level 1', 'Level 2', 'EV Charging Hub']
        slot_types = ['STANDARD', 'STANDARD', 'COMPACT', 'SUV', 'EV', 'ACCESSIBLE', 'VIP']

        total_created = 0
        total_reset = 0

        for floor in floors:
            prefix = 'G' if floor == 'Ground Floor' else ('L1' if floor == 'Level 1' else ('L2' if floor == 'Level 2' else 'EV'))
            for i in range(101, 111):
                slot_num = f"{prefix}-{i}"
                slot_type = 'EV' if floor == 'EV Charging Hub' else slot_types[(i % len(slot_types))]
                
                multiplier = 1.00
                if slot_type == 'EV':
                    multiplier = 1.40
                elif slot_type == 'VIP':
                    multiplier = 1.60

                slot, s_created = ParkingSlot.objects.get_or_create(
                    location=mall,
                    slot_number=slot_num,
                    defaults={
                        'floor': floor,
                        'slot_type': slot_type,
                        'status': 'AVAILABLE',  # ALL GREEN AVAILABLE!
                        'price_multiplier': multiplier,
                        'is_covered': True
                    }
                )

                if not s_created:
                    slot.status = 'AVAILABLE'  # Force ALL slots to GREEN AVAILABLE
                    slot.save()
                    total_reset += 1
                else:
                    total_created += 1

        self.stdout.write(self.style.SUCCESS('Successfully reset all parking slots to AVAILABLE (Green)! System is 100% fresh.'))
