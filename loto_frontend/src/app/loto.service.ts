import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from '@auth0/auth0-angular';
import { environment } from '../environments/environment';
import { Observable, switchMap } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class LotoService {
  private base = environment.apiBaseUrl;

  constructor(private http: HttpClient, private auth: AuthService) {}

  createTicket(owner_id: string, numbers: string): Observable<Blob> {
    return this.auth.getAccessTokenSilently().pipe(
      switchMap((token) => {
        const headers = new HttpHeaders({
          Authorization: `Bearer ${token}`,
        });

        return this.http.post(
          `${this.base}/tickets`,
          { owner_id, numbers },
          { responseType: 'blob', headers }
        );
      })
    );
  }

  getCurrentRound(): Observable<any> {
    return this.http.get(`${this.base}/ticket-status`);
  }
}
