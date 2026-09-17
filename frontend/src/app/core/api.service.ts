/** Access typed selection APIs using the configured application origin. */
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export interface Movie { id: string; title: string; poster_placeholder: string; }
export interface Theatre { id: string; name: string; }
export interface CreateBookingRequest { movie_id: string; theatre_id: string; seats: ['A1', 'A2', 'A3']; payment_method: 'CARD' | 'UPI'; }
export interface BookingConfirmation { booking_confirmation_id: string; movie: { id: string; title: string }; theatre: { id: string; name: string }; seats: string[]; total_price: string | number; payment_method: 'CARD' | 'UPI'; booked_at: string; }
interface MoviesResponse { movies: Movie[]; }
interface TheatresResponse { theatres: Theatre[]; }

/** Provide typed API methods for the booking selection journey. */
@Injectable({ providedIn: 'root' })
export class ApiService {
  /** Construct API access with Angular's HTTP client. */
  constructor(private readonly http: HttpClient) {}

  /** Return movies in the backend's canonical title order. */
  getMovies(): Observable<MoviesResponse> {
    return this.http.get<MoviesResponse>(`${environment.apiBaseUrl}/api/movies`);
  }

  /** Return theatres mapped to one selected movie. */
  getTheatres(movieId: string): Observable<TheatresResponse> {
    return this.http.get<TheatresResponse>(`${environment.apiBaseUrl}/api/theatres`, { params: { movie_id: movieId } });
  }

  /** Create a booking using only the strict server-approved payload. */
  createBooking(request: CreateBookingRequest): Observable<BookingConfirmation> {
    return this.http.post<BookingConfirmation>(`${environment.apiBaseUrl}/api/bookings`, request);
  }

  /** Read an authenticated customer's durable booking confirmation. */
  getBooking(confirmationId: string): Observable<BookingConfirmation> {
    return this.http.get<BookingConfirmation>(`${environment.apiBaseUrl}/api/bookings/${encodeURIComponent(confirmationId)}`);
  }
}
