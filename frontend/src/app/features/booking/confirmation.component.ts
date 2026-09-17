/** Render a database-backed booking confirmation from its route identifier. */
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { ApiService, BookingConfirmation } from '../../core/api.service';
import { BookingStore } from './booking.store';

/** Load an authenticated customer's durable confirmation and offer a clean restart. */
@Component({
  standalone: true,
  selector: 'app-confirmation',
  template: `<main class="page booking-page"><section class="panel catalogue-panel confirmation-panel"><p class="eyebrow">Booking confirmed</p>@if (confirmation(); as booking) {<h1>You're booked.</h1><p class="confirmation-id">{{ booking.booking_confirmation_id }}</p><dl class="confirmation-details"><div><dt>Movie</dt><dd>{{ booking.movie.title }}</dd></div><div><dt>Theatre</dt><dd>{{ booking.theatre.name }}</dd></div><div><dt>Seats</dt><dd>{{ booking.seats.join(', ') }}</dd></div><div><dt>Total</dt><dd>₹{{ booking.total_price }}</dd></div></dl><button class="button" type="button" (click)="startNewBooking()">Start new booking</button>} @else {<h1>Loading your booking…</h1><p class="status" aria-live="polite">{{ status() }}</p>}</section></main>`
})
export class ConfirmationComponent implements OnInit {
  /** Expose the durable confirmation read from the API. */
  readonly confirmation = signal<BookingConfirmation | null>(null);
  /** Announce loading and recoverable read states. */
  readonly status = signal('Loading your booking confirmation…');
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly store = inject(BookingStore);

  /** Read the parameterized confirmation through the authenticated API client. */
  ngOnInit(): void {
    const confirmationId = this.route.snapshot.paramMap.get('confirmationId');
    if (!confirmationId) {
      this.status.set('Booking confirmation could not be loaded.');
      return;
    }
    this.api.getBooking(confirmationId).subscribe({
      next: (confirmation) => { this.store.confirm(confirmation); this.confirmation.set(confirmation); },
      error: () => this.status.set('Booking confirmation could not be loaded.')
    });
  }

  /** Reset every draft field before returning to the catalogue. */
  startNewBooking(): void {
    this.store.reset();
    void this.router.navigate(['/movies']);
  }
}