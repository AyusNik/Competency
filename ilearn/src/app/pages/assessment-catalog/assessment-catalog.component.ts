import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { IlearnService } from '../../services/ilearn.service';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

@Component({
  selector: 'app-assessment-catalog',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './assessment-catalog.component.html',
  styleUrl: './assessment-catalog.component.scss'
})
export class AssessmentCatalogComponent implements OnInit {
  assessments: any[] = [];
  categories: string[] = ['All'];
  types = ['All', 'PLE', 'CPA', 'OJT'];
  search = '';
  selectedCategory = 'All';
  selectedType = 'All';
  loading = true;
  private search$ = new Subject<string>();

  constructor(private svc: IlearnService) {}

  ngOnInit() {
    this.svc.getCategories().subscribe(cats => this.categories = ['All', ...cats]);
    this.load();
    this.search$.pipe(debounceTime(300), distinctUntilChanged()).subscribe(() => this.load());
  }

  load() {
    this.loading = true;
    this.svc.getAssessments(this.search, this.selectedCategory, this.selectedType).subscribe(data => {
      this.assessments = data;
      this.loading = false;
    });
  }

  onSearch() { this.search$.next(this.search); }
  onCategory(cat: string) { this.selectedCategory = cat; this.load(); }
  onType(type: string) { this.selectedType = type; this.load(); }
}
