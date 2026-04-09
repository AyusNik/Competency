import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';

const API = 'http://localhost:8005/auth';

@Injectable({ providedIn: 'root' })
export class AuthService {
  constructor(private http: HttpClient, private router: Router) {}

  register(name: string, email: string, password: string, manager_title: string, manager_phone: string) {
    return this.http.post<any>(`${API}/register`, { name, email, password, manager_title, manager_phone }).pipe(
      tap(res => { localStorage.setItem('cat_token', res.access_token); localStorage.setItem('cat_name', res.name); })
    );
  }

  login(email: string, password: string) {
    return this.http.post<any>(`${API}/login`, { email, password }).pipe(
      tap(res => { localStorage.setItem('cat_token', res.access_token); localStorage.setItem('cat_name', res.name); })
    );
  }

  logout() { localStorage.removeItem('cat_token'); localStorage.removeItem('cat_name'); this.router.navigate(['/login']); }
  isLoggedIn(): boolean { return !!localStorage.getItem('cat_token'); }
  getName(): string { return localStorage.getItem('cat_name') || ''; }
}
