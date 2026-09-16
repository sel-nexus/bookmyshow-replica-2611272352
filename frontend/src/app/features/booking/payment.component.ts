/** Collect a local demo payment choice and create one durable booking. */
import { Component, OnDestroy, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription, timer } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { BookingStore } from './booking.store';

/** Render the protected payment step with local-only demo payment details. */
@Component({
  standalone: true,
  selector: 'app-payment',
  template: `<main class="page booking-page"><section class="panel catalogue-panel payment-panel"><p class="eyebrow">Final step</p><h1>Confirm payment</h1><p class="selected-context">{{ store.draft().movie?.title }} · {{ store.draft().theatre?.name }}</p><p class="price">{{ store.draft().seats.join(', ') }} · ₹{{ store.draft().totalPrice }}</p><fieldset><legend>Payment method</legend><label class="radio"><input type="radio" name="paymentMethod" value="CARD" [checked]="paymentMethod() === 'CARD'" (change)="setPaymentMethod('CARD')"> Card</label><label class="radio"><input type="radio" name="paymentMethod" value="UPI" [checked]="paymentMethod() === 'UPI'" (change)="setPaymentMethod('UPI')"> UPI</label></fieldset><label class="field" for="demo-instrument">{{ paymentMethod() === 'CARD' ? 'Demo card number' : 'Demo UPI ID' }}<input id="demo-instrument" [value]="instrument()" (input)="instrument.set($any($event.target).value)" autocomplete="off"></label><p class="demo-note">Demo-only payment detail. It is never sent to BookMyShow.</p><p class="status" aria-live="polite">{{ message() }}</p><button class="button" type="button" [disabled]="payDisabled()" (click)="pay()">{{ store.draft().phase === 'PROCESSING' ? 'Processing…' : 'Pay ₹450' }}</button></section></main>`
})
export class PaymentComponent implements OnDestroy {
  /** Expose selected booking state to the payment template. */
  readonly store = inject(BookingStore);
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  readonly paymentMethod = signal<'CARD' | 'UPI'>('CARD');
  readonly instrument = signal('');
  readonly message = signal('Choose a method and confirm your demo payment.');
  readonly payDisabled = signal(false);
  private processing?: Subscription;

  /** Set a local-only payment choice and retain it in the booking draft. */
  setPaymentMethod(method: 'CARD' | 'UPI'): void {
    this.paymentMethod.set(method);
    this.store.setPaymentMethod(method);
  }

  /** Start exactly one delayed request after ensuring the draft is complete. */
  pay(): void {
    const draft = this.store.draft();
    if (this.payDisabled() || !draft.movie || !draft.theatre || draft.seats.join(',') !== 'A1,A2,A3') {
      this.message.set('Choose a movie, theatre, and the fixed seats before paying.');
      return;
    }
    this.payDisabled.set(true);
    this.message.set('Processing your payment…');
    this.store.setPhase('PROCESSING');
    this.processing = timer(2000).subscribe(() => {
      this.api.createBooking({ movie_id: draft.movie!.id, theatre_id: draft.theatre!.id, seats: ['A1', 'A2', 'A3'], payment_method: this.paymentMethod() }).subscribe({
        next: (confirmation) => { this.store.confirm(confirmation); void this.router.navigate(['/confirmation']); },
        error: () => { this.store.setPhase('PAYMENT'); this.payDisabled.set(false); this.message.set('Payment could not be confirmed. Please try again.'); }
      });
    });
  }

  /** Cancel delayed work and clear local demo instrument data on teardown. */
  ngOnDestroy(): void {
    this.processing?.unsubscribe();
    this.instrument.set('');
  }
}