import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { CatalogComponent } from './pages/catalog/catalog.component';
import { AssessmentCatalogComponent } from './pages/assessment-catalog/assessment-catalog.component';
import { CourseDetailComponent } from './pages/course-detail/course-detail.component';
import { AssessmentDetailComponent } from './pages/assessment-detail/assessment-detail.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'courses', component: CatalogComponent },
  { path: 'courses/:id', component: CourseDetailComponent },
  { path: 'assessments', component: AssessmentCatalogComponent },
  { path: 'assessments/:id', component: AssessmentDetailComponent },
  { path: '**', redirectTo: '' },
];
