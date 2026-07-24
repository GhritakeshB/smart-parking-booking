import json
import secrets
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, Q
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import ParkingLocation, ParkingSlot, Booking, PaymentRecord

# Helper to check if user is staff/admin
def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

# ==================== AUTHENTICATION VIEWS ====================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'parking/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('login')


# ==================== PARKING VIEWS ====================

@login_required(login_url='login')
def index_view(request):
    mall = ParkingLocation.objects.filter(slug='grand-shopping-mall').first() or ParkingLocation.objects.first()
    
    total_slots = ParkingSlot.objects.count()
    available_slots = ParkingSlot.objects.filter(status='AVAILABLE').count()
    occupied_slots = ParkingSlot.objects.filter(status='OCCUPIED').count()
    reserved_slots = ParkingSlot.objects.filter(status='RESERVED').count()
    
    floors = list(ParkingSlot.objects.values_list('floor', flat=True).distinct().order_by('floor'))
    
    context = {
        'mall': mall,
        'floors': floors,
        'total_slots': total_slots,
        'available_slots': available_slots,
        'occupied_slots': occupied_slots,
        'reserved_slots': reserved_slots,
    }
    return render(request, 'parking/index.html', context)


# Worker Gatekeeper Entrance Check-In Terminal
@login_required(login_url='login')
def worker_entry_view(request):
    mall = ParkingLocation.objects.first()
    available_slots = ParkingSlot.objects.filter(status='AVAILABLE').order_by('floor', 'slot_number')
    
    context = {
        'mall': mall,
        'available_slots': available_slots,
        'now_iso': timezone.now().strftime('%Y-%m-%dT%H:%M'),
    }
    return render(request, 'parking/worker_entry.html', context)


# Admin / Worker Exit Gate Checkout Terminal
@login_required(login_url='login')
def worker_exit_view(request):
    active_bookings = Booking.objects.filter(status='ACTIVE').select_related('slot').order_by('-start_time')
    
    context = {
        'active_bookings': active_bookings,
    }
    return render(request, 'parking/worker_exit.html', context)


# ADMIN ONLY DASHBOARD VIEW & USER / ADMIN CREATOR
@login_required(login_url='login')
@user_passes_test(is_admin_user, login_url='index', redirect_field_name=None)
def admin_dashboard_view(request):
    # Handle Admin Creation of New Worker or 2nd Admin Account
    if request.method == 'POST' and 'action' in request.POST and request.POST['action'] == 'create_worker':
        worker_name = request.POST.get('worker_name', '').strip()
        worker_username = request.POST.get('worker_username', '').strip().lower()
        worker_password = request.POST.get('worker_password', '').strip()
        user_role = request.POST.get('user_role', 'worker')

        if not (worker_username and worker_password):
            messages.error(request, "Username and password are required.")
        elif User.objects.filter(username=worker_username).exists():
            messages.error(request, f"Username '{worker_username}' already exists.")
        else:
            if user_role == 'admin':
                new_user = User.objects.create_superuser(
                    username=worker_username,
                    email=f"{worker_username}@smartpark.com",
                    password=worker_password,
                    first_name=worker_name
                )
                messages.success(request, f"👑 2nd ADMIN Account '{worker_username}' created successfully! This user has FULL Admin & Analytics access.")
            else:
                new_user = User.objects.create_user(
                    username=worker_username,
                    password=worker_password,
                    first_name=worker_name
                )
                messages.success(request, f"🟢 Worker Account '{worker_username}' created successfully!")

            return redirect('admin_dashboard')

    total_slots = ParkingSlot.objects.count()
    available_slots = ParkingSlot.objects.filter(status='AVAILABLE').count()
    occupied_slots = ParkingSlot.objects.filter(status='OCCUPIED').count()
    reserved_slots = ParkingSlot.objects.filter(status='RESERVED').count()
    maintenance_slots = ParkingSlot.objects.filter(status='MAINTENANCE').count()
    
    occupancy_pct = round(((occupied_slots + reserved_slots) / total_slots * 100), 1) if total_slots > 0 else 0
    total_revenue = Booking.objects.aggregate(total=Sum('total_cost'))['total'] or 0.00
    
    recent_bookings = Booking.objects.all().order_by('-created_at')[:15]
    all_users = User.objects.all().order_by('-date_joined')
    
    context = {
        'total_slots': total_slots,
        'available_slots': available_slots,
        'occupied_slots': occupied_slots,
        'reserved_slots': reserved_slots,
        'maintenance_slots': maintenance_slots,
        'occupancy_pct': occupancy_pct,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
        'all_users': all_users,
    }
    return render(request, 'parking/admin_dashboard.html', context)


# ==================== REST API ENDPOINTS ====================

@csrf_exempt
def api_worker_checkin(request):
    """Worker Gate Registration: Sets Slot status = OCCUPIED in PostgreSQL"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        slot_id = data.get('slot_id')
        vehicle_number = data.get('vehicle_number', '').strip().upper()
        driver_name = data.get('driver_name', 'Walk-in Driver').strip()
        driver_phone = data.get('driver_phone', 'N/A').strip()
        vehicle_type = data.get('vehicle_type', 'Sedan')

        if not (slot_id and vehicle_number):
            return JsonResponse({'status': 'error', 'message': 'Please provide vehicle plate number and select a slot.'}, status=400)

        slot = get_object_or_404(ParkingSlot, pk=slot_id)

        if slot.status == 'OCCUPIED':
            return JsonResponse({'status': 'error', 'message': f'Slot {slot.slot_number} is already OCCUPIED.'}, status=400)

        now = timezone.now()
        est_end = now + timedelta(hours=2)

        booking = Booking.objects.create(
            slot=slot,
            driver_name=driver_name,
            driver_phone=driver_phone,
            vehicle_number=vehicle_number,
            vehicle_type=vehicle_type,
            start_time=now,
            end_time=est_end,
            total_hours=2.00,
            total_cost=round(2.00 * slot.effective_hourly_rate, 2),
            status='ACTIVE'
        )

        slot.status = 'OCCUPIED'
        slot.save()

        PaymentRecord.objects.create(
            booking=booking,
            transaction_id=f"TXN-ENTRY-{secrets.token_hex(4).upper()}",
            amount=booking.total_cost,
            payment_method='Gate Cash / Scanner'
        )

        return JsonResponse({
            'status': 'success',
            'message': f'Vehicle {vehicle_number} registered! Slot {slot.slot_number} is now marked OCCUPIED.',
            'booking_id': booking.booking_id,
            'slot_number': slot.slot_number,
            'entry_time': booking.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'qr_token': booking.qr_token
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_worker_checkout(request):
    """Admin/Worker Exit Gate Checkout: Sets Slot status = AVAILABLE (FREE) in PostgreSQL"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        slot_id = data.get('slot_id')

        booking = None
        if booking_id:
            booking = Booking.objects.filter(booking_id=booking_id, status='ACTIVE').first()
        elif slot_id:
            booking = Booking.objects.filter(slot_id=slot_id, status='ACTIVE').first()

        if not booking:
            if slot_id:
                slot = get_object_or_404(ParkingSlot, pk=slot_id)
                slot.status = 'AVAILABLE'
                slot.save()
                return JsonResponse({'status': 'success', 'message': f'Slot {slot.slot_number} marked FREE.'})
            return JsonResponse({'status': 'error', 'message': 'No active occupied record found for this slot/vehicle.'}, status=404)

        now = timezone.now()
        booking.end_time = now
        
        duration_seconds = (now - booking.start_time).total_seconds()
        hours = max(0.5, round(duration_seconds / 3600.0, 2))
        booking.total_hours = hours
        booking.total_cost = round(hours * booking.slot.effective_hourly_rate, 2)
        booking.status = 'COMPLETED'
        booking.save()

        slot = booking.slot
        slot.status = 'AVAILABLE'
        slot.save()

        return JsonResponse({
            'status': 'success',
            'message': f'Vehicle {booking.vehicle_number} checked out! Slot {slot.slot_number} is now marked FREE (AVAILABLE).',
            'booking_id': booking.booking_id,
            'slot_number': slot.slot_number,
            'total_hours': float(hours),
            'total_cost': float(booking.total_cost)
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def api_slots(request, slug=None):
    floor_filter = request.GET.get('floor', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')

    slots_qs = ParkingSlot.objects.all().order_by('floor', 'slot_number')
    if floor_filter:
        slots_qs = slots_qs.filter(floor=floor_filter)
    if type_filter:
        slots_qs = slots_qs.filter(slot_type=type_filter)
    if status_filter:
        slots_qs = slots_qs.filter(status=status_filter)

    slots_data = []
    for s in slots_qs:
        slots_data.append({
            'id': s.id,
            'slot_number': s.slot_number,
            'floor': s.floor,
            'slot_type': s.slot_type,
            'slot_type_display': s.get_slot_type_display(),
            'status': s.status,
            'effective_hourly_rate': s.effective_hourly_rate,
            'is_covered': s.is_covered,
        })

    return JsonResponse({
        'status': 'success',
        'slots': slots_data
    })
