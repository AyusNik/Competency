import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-ple-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ple-detail.component.html',
  styleUrl: './ple-detail.component.scss',
})
export class PleDetailComponent implements OnInit {
  examName = '';

  constructor(private route: ActivatedRoute, private router: Router) {}

  ngOnInit() {
    this.examName = this.route.snapshot.queryParamMap.get('exam') || 'PLE Assessment';
  }

  goBack() { this.router.navigate(['/dashboard']); }
}
