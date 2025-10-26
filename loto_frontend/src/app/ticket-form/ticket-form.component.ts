import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgIf } from '@angular/common';
import { LotoService } from '../loto.service';
import { AuthService } from '@auth0/auth0-angular';

@Component({
  selector: 'app-ticket-form',
  standalone: true,
  imports: [FormsModule, NgIf],
  templateUrl: './ticket-form.component.html',
  styleUrls: ['./ticket-form.component.css'],
})
export class TicketFormComponent {
  ownerId = '';
  numbers = '';

  qrCodeUrl: string | null = null;
  errorMessage: string | null = null;
  isSubmitting = false;

  constructor(private loto: LotoService, private auth: AuthService) {}

  onSubmit() {
    if (this.isSubmitting) {
      return;
    }

    this.errorMessage = null;
    this.qrCodeUrl = null;
    this.isSubmitting = true;

    if (!this.ownerId.trim()) {
      this.errorMessage = 'Molimo unesite broj osobne iskaznice ili putovnice';
      this.isSubmitting = false;
      return;
    }

    if (!this.numbers.trim()) {
      this.errorMessage = 'Molimo unesite brojeve odvojene zarezom';
      this.isSubmitting = false;
      return;
    }

    this.loto.createTicket(this.ownerId, this.numbers).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        this.qrCodeUrl = url;
        this.isSubmitting = false;
      },
      error: (err) => {
        if (err.status === 401) {
          this.errorMessage = 'Niste prijavljeni. Molimo prijavite se ponovno.';
        } else if (err.status === 400) {
          this.errorMessage =
            err.error?.detail ||
            'Neispravni podaci. Provjerite unesene brojeve.';
        } else if (err.error?.detail) {
          this.errorMessage = err.error.detail;
        } else {
          this.errorMessage = 'Greška pri uplati listića. Pokušajte ponovno.';
        }

        this.isSubmitting = false;
      },
    });
  }

  clearQRCode() {
    if (this.qrCodeUrl) {
      URL.revokeObjectURL(this.qrCodeUrl);
      this.qrCodeUrl = null;
    }
    this.ownerId = '';
    this.numbers = '';
    this.errorMessage = null;
  }
}
