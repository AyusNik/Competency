import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { IlearnService } from '../../services/ilearn.service';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

@Component({
  selector: 'app-catalog',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './catalog.component.html',
  styleUrl: './catalog.component.scss'
})
export class CatalogComponent implements OnInit {
  courses: any[] = [];
  categories: string[] = ['All'];
  search = '';
  selectedCategory = 'All';
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
    this.svc.getCourses(this.search, this.selectedCategory).subscribe(data => {
      this.courses = data;
      this.loading = false;
    });
  }

  onSearch() { this.search$.next(this.search); }
  onCategory(cat: string) { this.selectedCategory = cat; this.load(); }
}
