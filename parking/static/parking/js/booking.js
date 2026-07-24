/* ==========================================================================
   SMART PARKING SLOT BOOKING - DYNAMIC INTERACTIVE LOGIC
   ========================================================================== */

let selectedSlotId = null;
let selectedSlotRate = 0;
let selectedSlotNumber = '';

document.addEventListener('DOMContentLoaded', () => {
    initBookingPage();
});

function initBookingPage() {
    const slugElement = document.getElementById('locationSlug');
    if (!slugElement) return;

    const slug = slugElement.value;
    loadSlots(slug);

    // Floor and Type Filters
    document.querySelectorAll('.floor-filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.floor-filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            loadSlots(slug);
        });
    });

    document.querySelectorAll('.type-filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.type-filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            loadSlots(slug);
        });
    });

    // Time input change listeners
    const startTimeInput = document.getElementById('startTime');
    const endTimeInput = document.getElementById('endTime');

    if (startTimeInput && endTimeInput) {
        startTimeInput.addEventListener('change', calculateBookingCost);
        endTimeInput.addEventListener('change', calculateBookingCost);
    }

    // Form Submission
    const bookingForm = document.getElementById('parkingBookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', handleBookingSubmit);
    }
}

async function loadSlots(slug) {
    const gridContainer = document.getElementById('slotsGridContainer');
    if (!gridContainer) return;

    const activeFloorBtn = document.querySelector('.floor-filter-btn.active');
    const activeTypeBtn = document.querySelector('.type-filter-btn.active');

    const floor = activeFloorBtn ? activeFloorBtn.dataset.floor : '';
    const type = activeTypeBtn ? activeTypeBtn.dataset.type : '';

    let url = `/api/slots/${slug}/?`;
    if (floor) url += `floor=${encodeURIComponent(floor)}&`;
    if (type) url += `type=${encodeURIComponent(type)}&`;

    try {
        gridContainer.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 2rem; color: #94a3b8;">Loading interactive floor grid...</div>';
        
        const response = await fetch(url);
        const data = await response.json();

        if (data.status === 'success') {
            renderSlots(data.slots);
        } else {
            gridContainer.innerHTML = `<div style="grid-column: 1/-1; color: #ef4444;">Failed to load slots: ${data.message}</div>`;
        }
    } catch (err) {
        gridContainer.innerHTML = '<div style="grid-column: 1/-1; color: #ef4444;">Error connecting to parking slot server.</div>';
    }
}

function renderSlots(slots) {
    const gridContainer = document.getElementById('slotsGridContainer');
    gridContainer.innerHTML = '';

    if (slots.length === 0) {
        gridContainer.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 2rem; color: #94a3b8;">No slots match the selected criteria on this floor.</div>';
        return;
    }

    slots.forEach(slot => {
        const card = document.createElement('div');
        card.className = `slot-card ${slot.status} ${selectedSlotId === slot.id ? 'selected' : ''}`;
        card.dataset.id = slot.id;
        card.dataset.number = slot.slot_number;
        card.dataset.rate = slot.effective_hourly_rate;
        card.dataset.status = slot.status;

        let icon = '🚗';
        if (slot.slot_type === 'EV') icon = '⚡ EV';
        else if (slot.slot_type === 'SUV') icon = '🚙 SUV';
        else if (slot.slot_type === 'VIP') icon = '👑 VIP';
        else if (slot.slot_type === 'ACCESSIBLE') icon = '♿';

        card.innerHTML = `
            <div class="slot-num">${slot.slot_number}</div>
            <div class="slot-type-badge">${icon}</div>
            <div class="slot-price">₹${slot.effective_hourly_rate}/hr</div>
        `;

        if (slot.status === 'AVAILABLE') {
            card.addEventListener('click', () => selectSlot(slot, card));
        }

        gridContainer.appendChild(card);
    });
}

function selectSlot(slot, cardElement) {
    document.querySelectorAll('.slot-card').forEach(c => c.classList.remove('selected'));
    cardElement.classList.add('selected');

    selectedSlotId = slot.id;
    selectedSlotRate = slot.effective_hourly_rate;
    selectedSlotNumber = slot.slot_number;

    // Update Form Display
    const slotInput = document.getElementById('selectedSlotId');
    const displayNum = document.getElementById('selectedSlotDisplay');
    const submitBtn = document.getElementById('submitBookingBtn');

    if (slotInput) slotInput.value = slot.id;
    if (displayNum) displayNum.textContent = `${slot.slot_number} (${slot.slot_type_display})`;
    if (submitBtn) submitBtn.disabled = false;

    calculateBookingCost();
}

function calculateBookingCost() {
    const startTimeStr = document.getElementById('startTime')?.value;
    const endTimeStr = document.getElementById('endTime')?.value;

    const displayHours = document.getElementById('displayDurationHours');
    const displayTotalCost = document.getElementById('displayTotalCost');

    if (!startTimeStr || !endTimeStr || !selectedSlotRate) {
        if (displayHours) displayHours.textContent = '0 hrs';
        if (displayTotalCost) displayTotalCost.textContent = '₹0.00';
        return;
    }

    const start = new Date(startTimeStr);
    const end = new Date(endTimeStr);

    if (end <= start) {
        if (displayHours) displayHours.textContent = 'Invalid duration';
        if (displayTotalCost) displayTotalCost.textContent = '₹0.00';
        return;
    }

    const diffMs = end - start;
    const hours = Math.max(0.5, (diffMs / (1000 * 60 * 60)).toFixed(2));
    const totalCost = (hours * selectedSlotRate).toFixed(2);

    if (displayHours) displayHours.textContent = `${hours} hrs`;
    if (displayTotalCost) displayTotalCost.textContent = `₹${totalCost}`;
}

async function handleBookingSubmit(e) {
    e.preventDefault();

    if (!selectedSlotId) {
        alert('Please select an available parking slot from the floor map grid first.');
        return;
    }

    const driverName = document.getElementById('driverName').value;
    const driverPhone = document.getElementById('driverPhone').value;
    const vehicleNumber = document.getElementById('vehicleNumber').value;
    const vehicleType = document.getElementById('vehicleType').value;
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;

    const payload = {
        slot_id: selectedSlotId,
        driver_name: driverName,
        driver_phone: driverPhone,
        vehicle_number: vehicleNumber,
        vehicle_type: vehicleType,
        start_time: startTime,
        end_time: endTime
    };

    const submitBtn = document.getElementById('submitBookingBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = 'Processing Booking...';

    try {
        const response = await fetch('/api/booking/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        const resData = await response.json();

        if (resData.status === 'success') {
            showConfirmationModal(resData);
        } else {
            alert(`Booking Error: ${resData.message}`);
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Confirm & Reserve Slot';
        }
    } catch (err) {
        alert('Failed to connect to parking booking server.');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Confirm & Reserve Slot';
    }
}

function showConfirmationModal(data) {
    const modal = document.getElementById('bookingSuccessModal');
    if (modal) {
        document.getElementById('modalTicketId').textContent = data.booking_id;
        document.getElementById('modalSlotNum').textContent = data.slot_number;
        document.getElementById('modalTotalCost').textContent = `₹${data.total_cost}`;
        document.getElementById('modalBarcode').textContent = `||| | |||| | | || ${data.qr_token} ||`;
        
        modal.style.display = 'flex';
    } else {
        alert(`Booking Success! Ticket ID: ${data.booking_id}`);
        window.location.href = '/my-bookings/';
    }
}

// Checkout handler for my_bookings page
async function checkoutBooking(bookingId) {
    if (!confirm(`Confirm checkout for Booking Ticket ${bookingId}? This will release the slot.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/booking/${bookingId}/checkout/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const res = await response.json();
        if (res.status === 'success') {
            alert(res.message);
            window.location.reload();
        } else {
            alert(res.message);
        }
    } catch (err) {
        alert('Server error during checkout.');
    }
}
