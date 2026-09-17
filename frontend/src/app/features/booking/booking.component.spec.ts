import { provideRouter, Router } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { Movie, Theatre } from '../../core/api.service';
import { BookingStore } from './booking.store';
import { SeatsComponent } from './seats.component';

const movie: Movie = { id: 'movie-id', title: 'Paradise', poster_placeholder: '/assets/posters/paradise.svg' };
const theatre: Theatre = { id: 'theatre-id', name: 'Sandhya 70mm' };

describe('booking seat selection', () => {
  beforeEach(() => TestBed.configureTestingModule({ providers: [provideRouter([])] }));

  it('renders the canonical seats and total, then navigates to payment when the visible control is chosen', () => {
    const store = TestBed.inject(BookingStore);
    const navigate = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    store.selectMovie(movie);
    store.selectTheatre(theatre);
    const fixture = TestBed.createComponent(SeatsComponent);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[role="grid"]')?.textContent).toContain('A1');
    expect(fixture.nativeElement.textContent).toContain('3 seats · ₹450');
    (fixture.nativeElement.querySelector('button') as HTMLButtonElement).click();
    fixture.detectChanges();

    expect(navigate).toHaveBeenCalledWith(['/payment']);
    expect(store.draft().seats).toEqual(['A1', 'A2', 'A3']);
  });

  it('does not navigate to payment from an incomplete selection', () => {
    const navigate = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    const fixture = TestBed.createComponent(SeatsComponent);
    fixture.detectChanges();

    (fixture.nativeElement.querySelector('button') as HTMLButtonElement).click();
    fixture.detectChanges();

    expect(navigate).not.toHaveBeenCalled();
  });
});
