import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { IlearnService } from '../../services/ilearn.service';

@Component({
  selector: 'app-assessment-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './assessment-detail.component.html',
  styleUrl: './assessment-detail.component.scss'
})
export class AssessmentDetailComponent implements OnInit {
  assessment: any = null;
  loading = true;
  error = '';

  constructor(private route: ActivatedRoute, private svc: IlearnService) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.svc.getAssessment(id).subscribe({
      next: a => { this.assessment = a; this.loading = false; },
      error: () => { this.error = 'Assessment not found.'; this.loading = false; }
    });
  }
}
