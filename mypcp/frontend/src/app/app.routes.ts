import { Routes } from '@angular/router';
import { LoginComponent } from './pages/login/login.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { TrainingDetailComponent } from './pages/training-detail/training-detail.component';
import { PleDetailComponent } from './pages/ple-detail/ple-detail.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'training/:id', component: TrainingDetailComponent, canActivate: [authGuard] },
  { path: 'ple-detail', component: PleDetailComponent, canActivate: [authGuard] },
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: '**', redirectTo: 'dashboard' },
];
