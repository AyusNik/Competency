import { Component, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Router, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { filter } from 'rxjs';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, CommonModule],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.scss',
})
export class NavbarComponent implements OnInit {
  breadcrumb = 'Content Management';

  constructor(private router: Router, public auth: AuthService) {
    this.router.events.pipe(filter(e => e instanceof NavigationEnd)).subscribe((e: any) => {
      if (e.url.includes('training')) this.breadcrumb = 'Training Detail';
      else if (e.url.includes('fixed-step')) this.breadcrumb = 'Fixed Step Management';
      else this.breadcrumb = 'Content Management';
    });
  }

  ngOnInit() {}
}
