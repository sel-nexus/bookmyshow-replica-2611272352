/** Present the fixed seat policy and advance only after it is applied. */
import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';

import { BookingStore } from './booking.store';

/** Show a semantic visual seat grid for the bounded three-seat selection. */
@Component({
  standalone: true,
  selector: 'app-seats',
  template: `<main class="page booking-page"><section class="panel catalogue-panel"><p class="eyebrow">Step 3 of 3</p><h1>Your seats</h1><p class="selected-context">{{ store.draft().movie?.title }} · {{ store.draft().theatre?.name }}</p><div class="screen" aria-hidden="true">SCREEN THIS WAY</div><div class="seat-grid" role="grid" aria-label="Selected seats"><span role="gridcell" class="seat selected">A1</span><span role="gridcell" class="seat selected">A2</span><span role="gridcell" class="seat selected">A3</span></div><p class="price">3 seats · ₹450</p><button class="button" type="button" (click)="continueToPayment()">Continue to payment</button></section></main>`
})
export class SeatsComponent {
  /** Expose store state to the compact seat template. */
  readonly store = inject(BookingStore);
  private readonly router = inject(Router);

  /** Apply the canonical seats before advancing to the payment placeholder. */
  continueToPayment(): void {
    this.store.applyFixedSeats();
    if (this.store.draft().seats.length) void this.router.navigate(['/payment']);
  }
}

/** Render the bounded payment handoff notice for this implementation step. */
@Component({
  standalone: true,
  selector: 'app-payment-notice',
  template: `<main class="page booking-page"><section class="panel catalogue-panel"><p class="eyebrow">Selection saved</p><h1>Ready to pay</h1><p class="status">Payment setup is the next step.</p></section></main>`
})
export class PaymentNoticeComponent {}
