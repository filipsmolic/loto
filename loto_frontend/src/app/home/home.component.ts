import { Component, OnInit } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AsyncPipe, NgIf, NgFor } from '@angular/common';
import { AuthService } from '@auth0/auth0-angular';
import { LotoService } from '../loto.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [NgIf, NgFor, AsyncPipe, RouterLink],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
})
export class HomeComponent implements OnInit {
  ticketCount = 0;
  results: number[] | null = null;
  isActiveRound = false;

  constructor(
    public auth: AuthService,
    private router: Router,
    private lotoService: LotoService
  ) {}

  ngOnInit() {
    this.loadRoundStatus();
  }

  loadRoundStatus() {
    this.lotoService.getCurrentRound().subscribe({
      next: (data) => {
        this.ticketCount = data.ticket_count || 0;
        this.results = data.results || null;
        this.isActiveRound = data.active_round
          ? !data.active_round.closed
          : false;
      },
      error: (err) => {
        console.error('Error loading round status:', err);
      },
    });
  }

  get isLoggedIn(): boolean {
    let loggedIn = false;
    this.auth.isAuthenticated$.subscribe((isAuth) => {
      loggedIn = isAuth;
    });
    return loggedIn;
  }

  get hasResults(): boolean {
    return this.results !== null && this.results.length > 0;
  }

  goToForm() {
    this.router.navigate(['/ticket-form']);
  }
}
