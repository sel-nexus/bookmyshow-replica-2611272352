/** Hold transient booking selections across protected route navigation. */
import { Injectable, signal } from '@angular/core';

import { BookingConfirmation, Movie, Theatre } from '../../core/api.service';

export interface BookingDraft {
  movie?: Movie;
  theatre?: Theatre;
  seats: string[];
  totalPrice?: number;
  paymentMethod?: 'CARD' | 'UPI';
  confirmation?: BookingConfirmation;
  phase: 'MOVIES' | 'THEATRES' | 'SEATS' | 'PAYMENT' | 'PROCESSING' | 'CONFIRMED';
}

/** Store the LLD-defined booking draft and clear invalid downstream choices. */
@Injectable({ providedIn: 'root' })
export class BookingStore {
  /** Expose the active selection state as an Angular signal. */
  readonly draft = signal<BookingDraft>({ seats: [], phase: 'MOVIES' });

  /** Select a movie and reset theatre, seat, and payment state. */
  selectMovie(movie: Movie): void {
    this.draft.set({ movie, seats: [], phase: 'THEATRES' });
  }

  /** Select a mapped theatre and reset later choices. */
  selectTheatre(theatre: Theatre): void {
    const movie = this.draft().movie;
    if (movie) this.draft.set({ movie, theatre, seats: [], phase: 'SEATS' });
  }

  /** Apply the fixed seat and total policy before payment. */
  applyFixedSeats(): void {
    const { movie, theatre } = this.draft();
    if (movie && theatre) this.draft.set({ movie, theatre, seats: ['A1', 'A2', 'A3'], totalPrice: 450, phase: 'PAYMENT' });
  }

  /** Record the selected payment method without exposing payment instruments. */
  setPaymentMethod(paymentMethod: 'CARD' | 'UPI'): void {
    this.draft.update((draft) => ({ ...draft, paymentMethod }));
  }

  /** Move the current valid draft through a payment lifecycle phase. */
  setPhase(phase: BookingDraft['phase']): void {
    this.draft.update((draft) => ({ ...draft, phase }));
  }

  /** Keep the actual API confirmation for the confirmation route. */
  confirm(confirmation: BookingConfirmation): void {
    this.draft.update((draft) => ({ ...draft, paymentMethod: confirmation.payment_method, confirmation, phase: 'CONFIRMED' }));
  }

  /** Clear the whole in-memory draft for a new booking journey. */
  reset(): void {
    this.draft.set({ seats: [], phase: 'MOVIES' });
  }
}
