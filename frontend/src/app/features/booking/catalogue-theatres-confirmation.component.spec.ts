import { ActivatedRoute, provideRouter, Router, convertToParamMap } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { ApiService, Movie, Theatre } from '../../core/api.service';
import { BookingStore } from './booking.store';
import { CatalogueComponent } from './catalogue.component';
import { ConfirmationComponent } from './confirmation.component';
import { TheatresComponent } from './theatres.component';

const movie: Movie = { id: 'movie-id', title: 'Paradise', poster_placeholder: 'poster.svg' };
const theatre: Theatre = { id: 'theatre-id', name: 'Sandhya 70mm' };

describe('catalogue, theatre, and confirmation components', () => {
  let api: jasmine.SpyObj<ApiService>;
  let router: Router;
  let store: BookingStore;
  let routeSnapshot: { paramMap: ReturnType<typeof convertToParamMap> };

  beforeEach(() => {
    api = jasmine.createSpyObj<ApiService>('ApiService', ['getMovies', 'getTheatres', 'getBooking']);
    routeSnapshot = { paramMap: convertToParamMap({ confirmationId: 'BMS-20260916-ABC123' }) };
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: ApiService, useValue: api },
        { provide: ActivatedRoute, useValue: { snapshot: routeSnapshot } }
      ]
    });
    router = TestBed.inject(Router);
    store = TestBed.inject(BookingStore);
  });

  it('shows a user-visible catalogue loading failure when the API rejects the request', () => {
    api.getMovies.and.returnValue(throwError(() => new Error('offline')));
    const fixture = TestBed.createComponent(CatalogueComponent);

    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[aria-live="polite"]')?.textContent).toContain('Movies could not be loaded. Please try again.');
  });

  it('renders an empty catalogue response as an accessible prompt instead of stale choices', () => {
    api.getMovies.and.returnValue(of({ movies: [] }));
    const fixture = TestBed.createComponent(CatalogueComponent);

    fixture.detectChanges();

    expect(fixture.nativeElement.querySelectorAll('button.selection-card').length).toBe(0);
    expect(fixture.nativeElement.querySelector('[aria-live="polite"]')?.textContent).toContain('Select a movie to continue.');
  });

  it('selects a visible movie and navigates to theatre choices', () => {
    api.getMovies.and.returnValue(of({ movies: [movie] }));
    const navigate = spyOn(router, 'navigate').and.resolveTo(true);
    const fixture = TestBed.createComponent(CatalogueComponent);
    fixture.detectChanges();

    (fixture.nativeElement.querySelector('button[aria-label="Select Paradise"]') as HTMLButtonElement).click();

    expect(navigate).toHaveBeenCalledWith(['/theatres']);
    expect(store.draft().movie).toEqual(movie);
  });

  it('redirects an incomplete theatre journey back to the visible movie catalogue without calling the API', () => {
    const navigate = spyOn(router, 'navigate').and.resolveTo(true);
    const fixture = TestBed.createComponent(TheatresComponent);

    fixture.detectChanges();

    expect(navigate).toHaveBeenCalledWith(['/movies']);
    expect(api.getTheatres).not.toHaveBeenCalled();
  });

  it('announces a theatre API failure after a selected movie', () => {
    store.selectMovie(movie);
    api.getTheatres.and.returnValue(throwError(() => new Error('offline')));
    const fixture = TestBed.createComponent(TheatresComponent);

    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[aria-live="polite"]')?.textContent).toContain('Theatres could not be loaded. Please return to movies.');
  });

  it('announces a real empty theatre response without displaying a selectable theatre', () => {
    store.selectMovie(movie);
    api.getTheatres.and.returnValue(of({ theatres: [] }));
    const fixture = TestBed.createComponent(TheatresComponent);

    fixture.detectChanges();

    expect(fixture.nativeElement.querySelectorAll('button.selection-card').length).toBe(0);
    expect(fixture.nativeElement.querySelector('[aria-live="polite"]')?.textContent).toContain('No theatres are available for this movie.');
  });

  it('shows the confirmation recovery state without stale details when the route confirmation ID is missing', () => {
    const staleConfirmation = { booking_confirmation_id: 'BMS-STALE-DETAILS', movie, theatre, seats: ['A1', 'A2', 'A3'], total_price: '450.00', payment_method: 'CARD' as const, booked_at: '2026-09-16T10:00:00Z' };
    routeSnapshot.paramMap = convertToParamMap({});
    store.confirm(staleConfirmation);
    const fixture = TestBed.createComponent(ConfirmationComponent);

    fixture.detectChanges();

    expect(api.getBooking).not.toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('[aria-live="polite"]')?.textContent).toContain('Booking confirmation could not be loaded.');
    expect(fixture.nativeElement.querySelector('.confirmation-details')).toBeNull();
    expect(fixture.nativeElement.textContent).not.toContain('BMS-STALE-DETAILS');
  });

  it('shows the confirmation recovery state without stale details when loading the route confirmation fails', () => {
    const staleConfirmation = { booking_confirmation_id: 'BMS-STALE-DETAILS', movie, theatre, seats: ['A1', 'A2', 'A3'], total_price: '450.00', payment_method: 'CARD' as const, booked_at: '2026-09-16T10:00:00Z' };
    store.confirm(staleConfirmation);
    api.getBooking.and.returnValue(throwError(() => new Error('offline')));
    const fixture = TestBed.createComponent(ConfirmationComponent);

    fixture.detectChanges();

    expect(api.getBooking).toHaveBeenCalledWith('BMS-20260916-ABC123');
    expect(fixture.nativeElement.querySelector('[aria-live="polite"]')?.textContent).toContain('Booking confirmation could not be loaded.');
    expect(fixture.nativeElement.querySelector('.confirmation-details')).toBeNull();
    expect(fixture.nativeElement.textContent).not.toContain('BMS-STALE-DETAILS');
  });

  it('reads the route confirmation from the API before allowing a new booking', () => {
    const confirmation = { booking_confirmation_id: 'BMS-20260916-ABC123', movie, theatre, seats: ['A1', 'A2', 'A3'], total_price: '450.00', payment_method: 'CARD' as const, booked_at: '2026-09-16T10:00:00Z' };
    api.getBooking.and.returnValue(of(confirmation));
    const navigate = spyOn(router, 'navigate').and.resolveTo(true);
    const fixture = TestBed.createComponent(ConfirmationComponent);
    fixture.detectChanges();

    expect(api.getBooking).toHaveBeenCalledWith('BMS-20260916-ABC123');
    expect(fixture.nativeElement.textContent).toContain('BMS-20260916-ABC123');
    (fixture.nativeElement.querySelector('button') as HTMLButtonElement).click();

    expect(navigate).toHaveBeenCalledWith(['/movies']);
    expect(store.draft()).toEqual({ seats: [], phase: 'MOVIES' });
  });
});
