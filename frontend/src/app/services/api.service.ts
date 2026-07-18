import { Injectable } from '@angular/core';

// Shared API base configuration. TODO: read base URL from environment / rewrite rules.
@Injectable({ providedIn: 'root' })
export class ApiService {
  readonly baseUrl = '/api';
}
