import { Routes } from '@angular/router';
import { ContentManagementComponent } from './components/content-management/content-management.component';
import { FixedStepManagementComponent } from './components/fixed-step-management/fixed-step-management.component';
import { TrainingDetailComponent } from './components/training-detail/training-detail.component';
import { AssessmentDetailComponent } from './components/assessment-detail/assessment-detail.component';
import { LoginComponent } from './pages/login/login.component';
import { RegisterComponent } from './pages/register/register.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: '', redirectTo: 'content-management', pathMatch: 'full' },
  { path: 'content-management', component: ContentManagementComponent, canActivate: [authGuard] },
  { path: 'fixed-step-management', component: FixedStepManagementComponent, canActivate: [authGuard] },
  { path: 'training/:id', component: TrainingDetailComponent, canActivate: [authGuard] },
  { path: 'assessment/:id', component: AssessmentDetailComponent, canActivate: [authGuard] },
];
