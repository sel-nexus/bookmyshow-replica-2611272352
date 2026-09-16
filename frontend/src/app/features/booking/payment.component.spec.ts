/** Verify the payment delay, strict request, error, and teardown behavior. */
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { ApiService } from '../../core/api.service';
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

  it('waits 2000ms then sends one minimal canonical booking request', fakeAsync(() => {
    const fixture = TestBed.createComponent(PaymentComponent);
    fixture.componentInstance.pay();
    expect(fixture.componentInstance.payDisabled()).toBeTrue();
    fixture.componentInstance.pay();
    tick(1999); http.expectNone('/api/bookings');
    tick(1);
    const request = http.expectOne('/api/bookings');
    expect(request.request.body).toEqual({ movie_id: movie.id, theatre_id: theatre.id, seats: ['A1', 'A2', 'A3'], payment_method: 'CARD' });
    request.flush(response);
    expect(TestBed.inject(BookingStore).draft().phase).toBe('CONFIRMED');
  }));

  it('returns to payment and enables retry after a booking API error', fakeAsync(() => {
    const fixture = TestBed.createComponent(PaymentComponent);
    fixture.componentInstance.pay(); tick(2000);
    http.expectOne('/api/bookings').flush({ error: { code: 'INVALID_FIXED_SEATS' } }, { status: 422, statusText: 'Unprocessable Entity' });
    expect(fixture.componentInstance.payDisabled()).toBeFalse();
    expect(TestBed.inject(BookingStore).draft().phase).toBe('PAYMENT');
    expect(fixture.componentInstance.message()).toContain('could not be confirmed');
  }));

  it('cancels the delayed HTTP request when destroyed before 2000ms', fakeAsync(() => {
    const fixture = TestBed.createComponent(PaymentComponent);
    fixture.componentInstance.pay(); tick(1999);
    fixture.destroy(); tick(1);
    http.expectNone('/api/bookings');
  }));
});
