import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import {
  provideHttpClient,
  withInterceptorsFromDi,
} from '@angular/common/http';
import { provideAuth0 } from '@auth0/auth0-angular';
import { environment } from '../environments/environment';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptorsFromDi()),
    provideAuth0({
      domain: environment.auth.domain,
      clientId: environment.auth.clientId,
      authorizationParams: {
        redirect_uri: window.location.origin,
        audience: environment.auth.audience,
        scope: 'openid profile email',
      },
      httpInterceptor: {
        allowedList: [
          {
            uri: `${environment.apiBaseUrl}/*`,
            tokenOptions: {
              authorizationParams: {
                audience: environment.auth.audience,
              },
            },
          },
        ],
      },
    }),
  ],
};
