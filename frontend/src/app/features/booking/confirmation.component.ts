/** Render the server-returned durable booking confirmation. */
import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';

import { BookingStore } from './booking.store';

/** Show actual confirmation data and offer a clean booking restart. */
@Component({
  standalone: true,
  selector: 'app-confirmation',
  template: `<main class="page booking-page"><section class="panel catalogue-panel confirmation-panel"><p class="eyebrow">Booking confirmed</p>@if (store.draft().confirmation; as confirmation) {<h1>You're booked.</h1><p class="confirmation-id">{{ confirmation.booking_confirmation_id }}</p><dl class="confirmation-details"><div><dt>Movie</dt><dd>{{ confirmation.movie.title }}</dd></div><div><dt>Theatre</dt><dd>{{ confirmation.theatre.name }}</dd></div><div><dt>Seats</dt><dd>{{ confirmation.seats.join(', ') }}</dd></div><div><dt>Total</dt><dd>₹{{ confirmation.total_price }}</dd></div></dl><button class="button" type="button" (click)="startNewBooking()">Start new booking</button>} @else {<h1>No confirmation yet.</h1><p class="status">Complete a payment to view your booking confirmation.</p><button class="button" type="button" (click)="startNewBooking()">Choose a movie</button>}</section></main>`
})
export class ConfirmationComponent {
  /** Expose the durable confirmation held for this session. */
  readonly store = inject(BookingStore);
  private readonly router = inject(Router);

  /** Reset every draft field before returning to the catalogue. */
  startNewBooking(): void {
    this.store.reset();
    void this.router.navigate(['/movies']);
  }
}