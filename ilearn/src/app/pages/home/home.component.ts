import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { IlearnService } from '../../services/ilearn.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss'
})
export class HomeComponent implements OnInit {
  stats: any = {};
  featuredCourses: any[] = [];
  featuredAssessments: any[] = [];

  constructor(private svc: IlearnService) {}

  ngOnInit() {
    this.svc.getStats().subscribe(s => this.stats = s);
    this.svc.getCourses().subscribe(c => this.featuredCourses = c.slice(0, 4));
    this.svc.getAssessments().subscribe(a => this.featuredAssessments = a.slice(0, 3));
  }
}
