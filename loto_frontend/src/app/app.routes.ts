import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { TicketFormComponent } from './ticket-form/ticket-form.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'ticket-form', component: TicketFormComponent },
];
