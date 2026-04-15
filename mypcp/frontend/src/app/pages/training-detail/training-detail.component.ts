import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { DashboardService } from '../../services/dashboard.service';

@Component({
  selector: 'app-training-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './training-detail.component.html',
  styleUrl: './training-detail.component.scss',
})
export class TrainingDetailComponent implements OnInit {
  training: any = null;
  loading = true;
  error = '';

  constructor(private route: ActivatedRoute, private router: Router, private svc: DashboardService) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.svc.getTrainingDetail(id).subscribe({
      next: (t) => { this.training = t; this.loading = false; },
      error: () => { this.error = 'Training not found.'; this.loading = false; },
    });
  }

  openCourse(course: any) {
    window.open(`http://localhost:4201/courses/${course._id}`, '_blank');
  }

  goBack() { this.router.navigate(['/dashboard']); }
}
