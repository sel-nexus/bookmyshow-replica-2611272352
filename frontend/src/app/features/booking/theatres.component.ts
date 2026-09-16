/** Render theatres permitted for the selected movie. */
import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { ApiService, Theatre } from '../../core/api.service';
import { BookingStore } from './booking.store';

/** Require a selected movie, then load and choose its theatre mappings. */
@Component({
  standalone: true,
  selector: 'app-theatres',
  template: `<main class="page booking-page"><section class="panel catalogue-panel"><p class="eyebrow">Step 2 of 3</p><h1>Choose a theatre</h1><p class="selected-context">{{ movieTitle() }}</p><p class="status" aria-live="polite">{{ status() }}</p><div class="selection-grid">@for (theatre of theatres(); track theatre.id) {<button class="selection-card" type="button" (click)="select(theatre)" [attr.aria-label]="'Select ' + theatre.name"><strong>{{ theatre.name }}</strong><small>Available for this movie</small></button>}</div></section></main>`
})
export class TheatresComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly store = inject(BookingStore);
  private readonly router = inject(Router);
  readonly theatres = signal<Theatre[]>([]);
  readonly status = signal('Loading mapped theatres…');
  readonly movieTitle = signal('');

  /** Redirect incomplete journeys or fetch theatres for the chosen movie. */
  ngOnInit(): void {
    const movie = this.store.draft().movie;
    if (!movie) { void this.router.navigate(['/movies']); return; }
    this.movieTitle.set(movie.title);
    this.api.getTheatres(movie.id).subscribe({ next: (response) => { this.theatres.set(response.theatres); this.status.set(response.theatres.length ? 'Select a theatre to continue.' : 'No theatres are available for this movie.'); }, error: () => this.status.set('Theatres could not be loaded. Please return to movies.') });
  }

  /** Save an approved theatre and advance to the fixed-seat display. */
  select(theatre: Theatre): void {
    this.store.selectTheatre(theatre);
    void this.router.navigate(['/seats']);
  }
}
