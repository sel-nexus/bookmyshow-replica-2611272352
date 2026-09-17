import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { BookingStore } from './booking.store';
import { PaymentComponent } from './payment.component';

const movie = { id: 'movie-id', title: 'Paradise', poster_placeholder: '/assets/posters/paradise.svg' };
const theatre = { id: 'theatre-id', name: 'Sandhya 70mm' };
const response = { booking_confirmation_id: 'BMS-20260916-ABC123', movie: { id: movie.id, title: movie.title }, theatre: { id: theatre.id, name: theatre.name }, seats: ['A1', 'A2', 'A3'], total_price: '450.00', payment_method: 'CARD' as const, booked_at: '2026-09-16T10:00:00Z' };

describe('PaymentComponent', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()] });
    const store = TestBed.inject(BookingStore);
    store.selectMovie(movie); store.selectTheatre(theatre); store.applyFixedSeats();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('shows disabled processing feedback, then sends one minimal canonical booking request', fakeAsync(() => {
    const navigate = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    const fixture = TestBed.createComponent(PaymentComponent);
    fixture.detectChanges();
    (fixture.nativeElement.querySelector('button') as HTMLButtonElement).click();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Processing…');
    expect((fixture.nativeElement.querySelector('button') as HTMLButtonElement).disabled).toBeTrue();
    tick(1999); http.expectNone('/api/bookings');
    tick(1);
    const request = http.expectOne('/api/bookings');
    expect(request.request.body).toEqual({ movie_id: movie.id, theatre_id: theatre.id, seats: ['A1', 'A2', 'A3'], payment_method: 'CARD' });
    request.flush(response);
    expect(TestBed.inject(BookingStore).draft().phase).toBe('CONFIRMED');
    expect(navigate).toHaveBeenCalledWith(['/confirmation', response.booking_confirmation_id]);
  }));

  it('returns to payment, enables the visible retry control, and announces an API failure', fakeAsync(() => {
    const fixture = TestBed.createComponent(PaymentComponent);
    fixture.detectChanges();
    (fixture.nativeElement.querySelector('button') as HTMLButtonElement).click(); tick(2000);
    http.expectOne('/api/bookings').flush({ error: { code: 'INVALID_FIXED_SEATS' } }, { status: 422, statusText: 'Unprocessable Entity' });
    fixture.detectChanges();

    expect((fixture.nativeElement.querySelector('button') as HTMLButtonElement).disabled).toBeFalse();
    expect(fixture.nativeElement.querySelector('[aria-live="polite"]')?.textContent).toContain('Payment could not be confirmed. Please try again.');
  }));

  it('cancels the delayed HTTP request when destroyed before 2000ms', fakeAsync(() => {
    const fixture = TestBed.createComponent(PaymentComponent);
    fixture.componentInstance.pay(); tick(1999);
    fixture.destroy(); tick(1);
    expect(http.match('/api/bookings')).toHaveSize(0);
  }));

  it('does not send a booking for an incomplete journey and announces what is needed', () => {
    TestBed.inject(BookingStore).reset();
    const fixture = TestBed.createComponent(PaymentComponent);
    fixture.detectChanges();
    (fixture.nativeElement.querySelector('button') as HTMLButtonElement).click();
    fixture.detectChanges();

    http.expectNone('/api/bookings');
    expect(fixture.nativeElement.querySelector('[aria-live="polite"]')?.textContent).toContain('Choose a movie, theatre, and the fixed seats before paying.');
  });
});
