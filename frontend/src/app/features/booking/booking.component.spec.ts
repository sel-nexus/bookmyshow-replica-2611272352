/** Verify selection state transitions and the fixed-seat presentation. */
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { Movie, Theatre } from '../../core/api.service';
import { BookingStore } from './booking.store';
import { SeatsComponent } from './seats.component';

const movie: Movie = { id: 'movie-id', title: 'Paradise', poster_placeholder: '/assets/posters/paradise.svg' };
const theatre: Theatre = { id: 'theatre-id', name: 'Sandhya 70mm' };

describe('booking selection', () => {
  beforeEach(() => TestBed.configureTestingModule({ providers: [provideRouter([])] }));

  it('resets downstream selections when the movie changes', () => {
    const store = TestBed.inject(BookingStore);
    store.selectMovie(movie);
    store.selectTheatre(theatre);
    store.applyFixedSeats();
    store.selectMovie({ ...movie, id: 'other-movie', title: 'OG2' });
    expect(store.draft()).toEqual({ movie: { ...movie, id: 'other-movie', title: 'OG2' }, seats: [], phase: 'THEATRES' });
  });

  it('renders and applies exactly the canonical fixed seats and total', () => {
    const store = TestBed.inject(BookingStore);
    store.selectMovie(movie);
    store.selectTheatre(theatre);
    const fixture = TestBed.createComponent(SeatsComponent);
    fixture.componentInstance.continueToPayment();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('A1');
    expect(fixture.nativeElement.textContent).toContain('A2');
    expect(fixture.nativeElement.textContent).toContain('A3');
    expect(store.draft().seats).toEqual(['A1', 'A2', 'A3']);
    expect(store.draft().totalPrice).toBe(450);
    expect(store.draft().phase).toBe('PAYMENT');
  });
});
